# %% [markdown]
# # Attention UNet for DDR Diabetic Retinopathy Lesion Segmentation
#
# Kaggle-compatible training script for four lesion classes:
# HE, EX, MA, SE. The OD optic-disc labels are intentionally excluded.
#
# Outputs in /kaggle/working:
# - attention_unet_dr.pth
# - training_history.json
# - validation_samples.png

# %%
import json
import os
import random
import re
import time
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torch.amp import GradScaler, autocast
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from postprocess_masks import postprocess_multiclass_masks

try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
except ImportError as exc:
    raise ImportError(
        "Albumentations is required. In Kaggle, run: "
        "!pip install albumentations opencv-python-headless --quiet"
    ) from exc


# %% [markdown]
# ## Configuration

# %%
SEED = 42
DATA_ROOT = Path("/kaggle/input/datasets/sunfish141/ddr-segmentation")
LOCAL_DATA_ROOT = Path("data/archive")
LESION_ROOT = DATA_ROOT / "lesion_segmentation"
OUTPUT_DIR = Path("/kaggle/working")

if not LESION_ROOT.exists() and (LOCAL_DATA_ROOT / "lesion_segmentation").exists():
    LESION_ROOT = LOCAL_DATA_ROOT / "lesion_segmentation"
    OUTPUT_DIR = Path("outputs/kaggle_train")

LESION_CLASSES = ["HE", "EX", "MA", "SE"]
NUM_CLASSES = len(LESION_CLASSES)
IMAGE_SIZE = 512

BATCH_SIZE = 8
GRAD_ACCUM_STEPS = 1
EPOCHS = 50
LR = 1e-4
EARLY_STOP_PATIENCE = 15
NUM_WORKERS = 2
THRESHOLD = 0.5
MODEL_FEATURES = (32, 64, 128, 256)
POS_WEIGHT_POWER = 0.5
MAX_POS_WEIGHT = 50.0
CLASS_WEIGHT_MULTIPLIER = (1.0, 1.0, 3.0, 1.0)
LOSS_MASK_DILATION = {"HE": 1, "EX": 1, "MA": 1, "SE": 1}
EVAL_THRESHOLDS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)

MODEL_PATH = OUTPUT_DIR / "attention_unet_dr.pth"
BEST_LOSS_MODEL_PATH = OUTPUT_DIR / "attention_unet_dr_full_best_loss.pth"
BEST_DICE_MODEL_PATH = OUTPUT_DIR / "attention_unet_dr_full_best_dice.pth"
HISTORY_PATH = OUTPUT_DIR / "training_history_full.json"
THRESHOLDS_PATH = OUTPUT_DIR / "recommended_thresholds_full.json"
SAMPLES_PATH = OUTPUT_DIR / "validation_samples_full.png"

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = True


seed_everything(SEED)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_AMP = device.type == "cuda"
print(f"PyTorch: {torch.__version__}")
print(f"Device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"AMP enabled: {USE_AMP}")
print(f"Model features: {MODEL_FEATURES}")
print(f"Image size: {IMAGE_SIZE}")
print(f"Batch size: {BATCH_SIZE} x grad_accum {GRAD_ACCUM_STEPS} = {BATCH_SIZE * GRAD_ACCUM_STEPS}")
print(f"Data root: {LESION_ROOT}")


# %% [markdown]
# ## Dataset and Transforms

# %%
def find_image_files(image_dir: Path) -> list[Path]:
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
    return sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in image_exts
    )


def normalize_stem(stem: str) -> str:
    normalized = stem.lower()
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return normalized


def mask_key_variants(mask_path: Path, lesion: str) -> set[str]:
    stem = mask_path.stem
    lesion_lower = lesion.lower()
    variants = {normalize_stem(stem)}

    suffix_patterns = [
        rf"[_\-. ]?{lesion_lower}$",
        rf"[_\-. ]?mask$",
        rf"[_\-. ]?label$",
    ]
    lower_stem = stem.lower()
    for pattern in suffix_patterns:
        stripped = re.sub(pattern, "", lower_stem, flags=re.IGNORECASE)
        variants.add(normalize_stem(stripped))

    # DDR mirrors sometimes append class names or mask words in different order.
    for token in [lesion_lower, "mask", "label", "lesion"]:
        stripped = re.sub(rf"(^|[_\-. ]){token}([_\-. ]|$)", " ", lower_stem)
        variants.add(normalize_stem(stripped))

    return {variant for variant in variants if variant}


def build_mask_index(label_dir: Path, lesion: str) -> dict[str, Path]:
    mask_exts = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}
    mask_index: dict[str, Path] = {}
    for mask_path in sorted(label_dir.rglob("*")):
        if not mask_path.is_file() or mask_path.suffix.lower() not in mask_exts:
            continue
        for key in mask_key_variants(mask_path, lesion):
            mask_index.setdefault(key, mask_path)
    return mask_index


def read_rgb_image(image_path: Path) -> np.ndarray:
    with Image.open(image_path) as image:
        return np.array(image.convert("RGB"))


def read_binary_mask(mask_path: Path) -> np.ndarray:
    with Image.open(mask_path) as mask_image:
        mask = np.array(mask_image)
    if mask.ndim == 3:
        mask = mask[..., 0]
    return (mask > 0).astype(np.uint8)


def with_supported_kwargs(transform_cls, **kwargs):
    supported = transform_cls.__init__.__code__.co_varnames
    return transform_cls(**{key: value for key, value in kwargs.items() if key in supported})


class DDRLesionDataset(Dataset):
    def __init__(self, split: str, transform: A.Compose | None = None) -> None:
        self.split = split
        self.transform = transform
        self.image_dir = LESION_ROOT / split / "image"
        self.label_dirs = {
            lesion: LESION_ROOT / split / "label" / lesion
            for lesion in LESION_CLASSES
        }
        self.image_paths = find_image_files(self.image_dir)
        self.mask_indexes = {
            lesion: build_mask_index(self.label_dirs[lesion], lesion)
            for lesion in LESION_CLASSES
        }
        self.image_keys = {path: normalize_stem(path.stem) for path in self.image_paths}

        if not self.image_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {self.image_dir}")
        if not self.image_paths:
            raise FileNotFoundError(f"No images found in: {self.image_dir}")

        missing_dirs = [str(path) for path in self.label_dirs.values() if not path.exists()]
        if missing_dirs:
            raise FileNotFoundError(f"Missing label directories: {missing_dirs}")

        print(f"{split}: {len(self.image_paths)} images")
        for lesion in LESION_CLASSES:
            matched = sum(
                1
                for image_path in self.image_paths
                if self.image_keys[image_path] in self.mask_indexes[lesion]
            )
            print(
                f"  {lesion}: {len(self.mask_indexes[lesion])} mask files, "
                f"{matched} matched to images"
            )

    def __len__(self) -> int:
        return len(self.image_paths)

    def get_mask_path(self, image_path: Path, lesion: str) -> Path | None:
        return self.mask_indexes[lesion].get(self.image_keys[image_path])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        image_path = self.image_paths[index]
        image = read_rgb_image(image_path)
        height, width = image.shape[:2]

        masks = []
        for lesion in LESION_CLASSES:
            mask_path = self.get_mask_path(image_path, lesion)
            if mask_path is None:
                mask = np.zeros((height, width), dtype=np.uint8)
            else:
                mask = read_binary_mask(mask_path)
                if mask.shape[:2] != (height, width):
                    mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST)
            masks.append(mask)

        mask = np.stack(masks, axis=-1).astype(np.float32)

        if self.transform is not None:
            augmented = self.transform(image=image, mask=mask)
            image_tensor = augmented["image"].float()
            mask_aug = augmented["mask"]
            if isinstance(mask_aug, torch.Tensor):
                mask_tensor = mask_aug.float()
                if mask_tensor.ndim == 3 and mask_tensor.shape[-1] == NUM_CLASSES:
                    mask_tensor = mask_tensor.permute(2, 0, 1)
            else:
                mask_tensor = torch.from_numpy(mask_aug).float().permute(2, 0, 1)
        else:
            image_tensor = torch.from_numpy(image.transpose(2, 0, 1)).float() / 255.0
            mask_tensor = torch.from_numpy(mask.transpose(2, 0, 1)).float()

        return image_tensor, mask_tensor


train_transform = A.Compose(
    [
        A.Resize(IMAGE_SIZE, IMAGE_SIZE, interpolation=cv2.INTER_LINEAR),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        with_supported_kwargs(
            A.Affine,
            translate_percent={"x": (-0.05, 0.05), "y": (-0.05, 0.05)},
            scale=(0.90, 1.10),
            rotate=(-25, 25),
            border_mode=cv2.BORDER_CONSTANT,
            value=0,
            mask_value=0,
            fill=0,
            fill_mask=0,
            p=0.5,
        ),
        with_supported_kwargs(
            A.ElasticTransform,
            alpha=40,
            sigma=6,
            alpha_affine=10,
            border_mode=cv2.BORDER_CONSTANT,
            value=0,
            mask_value=0,
            fill=0,
            fill_mask=0,
            p=0.25,
        ),
        A.RandomBrightnessContrast(
            brightness_limit=0.20,
            contrast_limit=0.20,
            p=0.5,
        ),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ]
)

valid_transform = A.Compose(
    [
        A.Resize(IMAGE_SIZE, IMAGE_SIZE, interpolation=cv2.INTER_LINEAR),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ]
)

train_dataset = DDRLesionDataset("train", transform=train_transform)
valid_dataset = DDRLesionDataset("valid", transform=valid_transform)


def inspect_masks(dataset: DDRLesionDataset) -> dict[str, dict[str, int]]:
    stats = {
        lesion: {"matched": 0, "nonempty": 0, "pixels": 0}
        for lesion in LESION_CLASSES
    }
    print(f"\nMask sanity check: {dataset.split}")
    for image_path in tqdm(dataset.image_paths, desc=f"Inspect {dataset.split}", leave=False):
        image = read_rgb_image(image_path)
        height, width = image.shape[:2]
        for lesion in LESION_CLASSES:
            mask_path = dataset.get_mask_path(image_path, lesion)
            if mask_path is None:
                continue
            stats[lesion]["matched"] += 1
            mask = read_binary_mask(mask_path)
            if mask.shape[:2] != (height, width):
                mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST)
            pixel_count = int(mask.sum())
            stats[lesion]["pixels"] += pixel_count
            if pixel_count > 0:
                stats[lesion]["nonempty"] += 1

    for lesion in LESION_CLASSES:
        lesion_stats = stats[lesion]
        print(
            f"  {lesion}: matched={lesion_stats['matched']}, "
            f"nonempty={lesion_stats['nonempty']}, pixels={lesion_stats['pixels']}"
        )
        if lesion_stats["matched"] == 0:
            raise RuntimeError(f"No mask files matched for {dataset.split}/{lesion}.")
        if lesion_stats["nonempty"] == 0:
            raise RuntimeError(
                f"All masks are empty for {dataset.split}/{lesion}. "
                "Check mask paths and TIFF reading before training."
            )
    return stats


train_mask_stats = inspect_masks(train_dataset)
valid_mask_stats = inspect_masks(valid_dataset)


def compute_resized_pos_weight(dataset: DDRLesionDataset) -> torch.Tensor:
    positive_pixels = np.zeros(NUM_CLASSES, dtype=np.float64)
    total_pixels = len(dataset.image_paths) * IMAGE_SIZE * IMAGE_SIZE

    print("\nComputing resized positive weights")
    for image_path in tqdm(dataset.image_paths, desc="Pos weight", leave=False):
        for class_index, lesion in enumerate(LESION_CLASSES):
            mask_path = dataset.get_mask_path(image_path, lesion)
            if mask_path is None:
                continue
            mask = read_binary_mask(mask_path)
            mask = cv2.resize(
                mask,
                (IMAGE_SIZE, IMAGE_SIZE),
                interpolation=cv2.INTER_NEAREST,
            )
            positive_pixels[class_index] += float(mask.sum())

    negative_pixels = total_pixels - positive_pixels
    raw_pos_weight = negative_pixels / np.maximum(positive_pixels, 1.0)
    pos_weight = np.power(raw_pos_weight, POS_WEIGHT_POWER)
    pos_weight = pos_weight * np.array(CLASS_WEIGHT_MULTIPLIER, dtype=np.float64)
    pos_weight = np.clip(pos_weight, 1.0, MAX_POS_WEIGHT)

    for class_index, lesion in enumerate(LESION_CLASSES):
        print(
            f"  {lesion}: resized_positive_pixels={int(positive_pixels[class_index])}, "
            f"raw_pos_weight={raw_pos_weight[class_index]:.2f}, "
            f"multiplier={CLASS_WEIGHT_MULTIPLIER[class_index]:.1f}, "
            f"effective_pos_weight={pos_weight[class_index]:.2f}"
        )

    return torch.tensor(pos_weight, dtype=torch.float32)


POS_WEIGHT = compute_resized_pos_weight(train_dataset).to(device)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
    drop_last=False,
)
valid_loader = DataLoader(
    valid_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
    drop_last=False,
)

print(f"Train batches: {len(train_loader)}")
print(f"Valid batches: {len(valid_loader)}")


# %% [markdown]
# ## Attention UNet

# %%
class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class AttentionGate(nn.Module):
    def __init__(self, gate_channels: int, skip_channels: int, inter_channels: int) -> None:
        super().__init__()
        self.gate_proj = nn.Sequential(
            nn.Conv2d(gate_channels, inter_channels, kernel_size=1, bias=True),
            nn.BatchNorm2d(inter_channels),
        )
        self.skip_proj = nn.Sequential(
            nn.Conv2d(skip_channels, inter_channels, kernel_size=1, bias=True),
            nn.BatchNorm2d(inter_channels),
        )
        self.attention = nn.Sequential(
            nn.Conv2d(inter_channels, 1, kernel_size=1, bias=True),
            nn.BatchNorm2d(1),
            nn.Sigmoid(),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, gate: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        if gate.shape[2:] != skip.shape[2:]:
            gate = F.interpolate(
                gate,
                size=skip.shape[2:],
                mode="bilinear",
                align_corners=False,
            )

        energy = self.relu(self.gate_proj(gate) + self.skip_proj(skip))
        attention = self.attention(energy)
        return skip * attention


class UpBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.attention = AttentionGate(
            gate_channels=out_channels,
            skip_channels=skip_channels,
            inter_channels=max(out_channels // 2, 1),
        )
        self.conv = ConvBlock(out_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        if x.shape[2:] != skip.shape[2:]:
            x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        skip = self.attention(x, skip)
        return self.conv(torch.cat([skip, x], dim=1))


class AttentionUNet(nn.Module):
    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 4,
        features: tuple[int, int, int, int] = (64, 128, 256, 512),
    ) -> None:
        super().__init__()
        f1, f2, f3, f4 = features

        self.enc1 = ConvBlock(in_channels, f1)
        self.enc2 = ConvBlock(f1, f2)
        self.enc3 = ConvBlock(f2, f3)
        self.enc4 = ConvBlock(f3, f4)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        self.bridge = ConvBlock(f4, f4 * 2)

        self.up4 = UpBlock(f4 * 2, f4, f4)
        self.up3 = UpBlock(f4, f3, f3)
        self.up2 = UpBlock(f3, f2, f2)
        self.up1 = UpBlock(f2, f1, f1)
        self.out = nn.Conv2d(f1, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input_size = x.shape[2:]

        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool(enc1))
        enc3 = self.enc3(self.pool(enc2))
        enc4 = self.enc4(self.pool(enc3))

        bridge = self.bridge(self.pool(enc4))

        dec4 = self.up4(bridge, enc4)
        dec3 = self.up3(dec4, enc3)
        dec2 = self.up2(dec3, enc2)
        dec1 = self.up1(dec2, enc1)
        logits = self.out(dec1)

        if logits.shape[2:] != input_size:
            logits = F.interpolate(
                logits,
                size=input_size,
                mode="bilinear",
                align_corners=False,
            )
        return logits


model = AttentionUNet(
    in_channels=3,
    out_channels=NUM_CLASSES,
    features=MODEL_FEATURES,
).to(device)
total_params = sum(parameter.numel() for parameter in model.parameters())
trainable_params = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
print(f"Total parameters: {total_params:,}")
print(f"Trainable parameters: {trainable_params:,}")


# %% [markdown]
# ## Loss and Metrics

# %%
class FocalLoss(nn.Module):
    def __init__(
        self,
        alpha: float = 0.75,
        gamma: float = 2.0,
        pos_weight: torch.Tensor | None = None,
    ) -> None:
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        if pos_weight is not None:
            self.register_buffer("pos_weight", pos_weight.view(1, -1, 1, 1))
        else:
            self.pos_weight = None

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        probabilities = torch.sigmoid(logits)
        p_t = probabilities * targets + (1.0 - probabilities) * (1.0 - targets)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        focal_weight = alpha_t * torch.pow(1.0 - p_t, self.gamma)
        if self.pos_weight is not None:
            bce = torch.where(targets > 0.5, bce * self.pos_weight, bce)
        return (focal_weight * bce).mean()


@torch.no_grad()
def dice_by_class(
    logits: torch.Tensor,
    targets: torch.Tensor,
    threshold: float = THRESHOLD,
    eps: float = 1e-7,
) -> tuple[np.ndarray, np.ndarray]:
    predictions = (torch.sigmoid(logits) > threshold).float()
    scores = np.zeros(NUM_CLASSES, dtype=np.float64)
    counts = np.zeros(NUM_CLASSES, dtype=np.int64)

    for class_index in range(NUM_CLASSES):
        pred_class = predictions[:, class_index].reshape(predictions.shape[0], -1)
        target_class = targets[:, class_index].reshape(targets.shape[0], -1)
        target_sum = target_class.sum(dim=1)
        valid = target_sum > 0

        if valid.any():
            pred_valid = pred_class[valid]
            target_valid = target_class[valid]
            intersection = (pred_valid * target_valid).sum(dim=1)
            denominator = pred_valid.sum(dim=1) + target_valid.sum(dim=1)
            dice = (2.0 * intersection + eps) / (denominator + eps)
            scores[class_index] = dice.sum().item()
            counts[class_index] = int(valid.sum().item())

    return scores, counts


@torch.no_grad()
def predicted_positive_rate(
    logits: torch.Tensor,
    threshold: float = THRESHOLD,
) -> np.ndarray:
    predictions = (torch.sigmoid(logits) > threshold).float()
    rates = predictions.flatten(2).mean(dim=(0, 2))
    return rates.detach().cpu().numpy()


def make_loss_targets(masks: torch.Tensor) -> torch.Tensor:
    targets = masks
    dilated_channels = []
    needs_stack = False
    for class_index, lesion in enumerate(LESION_CLASSES):
        radius = LOSS_MASK_DILATION.get(lesion, 0)
        channel = targets[:, class_index : class_index + 1]
        if radius > 0:
            kernel_size = radius * 2 + 1
            channel = F.max_pool2d(
                channel,
                kernel_size=kernel_size,
                stride=1,
                padding=radius,
            )
            needs_stack = True
        dilated_channels.append(channel)
    if not needs_stack:
        return masks
    return torch.cat(dilated_channels, dim=1)


def best_threshold_summary(
    score_sums: dict[float, np.ndarray],
    count_sums: dict[float, np.ndarray],
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for class_index, lesion in enumerate(LESION_CLASSES):
        best_threshold = EVAL_THRESHOLDS[0]
        best_dice = 0.0
        for threshold in EVAL_THRESHOLDS:
            counts = count_sums[threshold]
            dice = (
                float(score_sums[threshold][class_index] / counts[class_index])
                if counts[class_index] > 0
                else 0.0
            )
            if dice > best_dice:
                best_dice = dice
                best_threshold = threshold
        summary[lesion] = {
            "threshold": float(best_threshold),
            "dice": float(best_dice),
        }
    return summary


def divide_scores(scores: np.ndarray, counts: np.ndarray) -> list[float]:
    return [
        float(scores[index] / counts[index]) if counts[index] > 0 else 0.0
        for index in range(len(scores))
    ]


criterion = FocalLoss(alpha=0.75, gamma=2.0, pos_weight=POS_WEIGHT)
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=5,
    min_lr=1e-7,
)
scaler = GradScaler("cuda", enabled=USE_AMP)


# %% [markdown]
# ## Training and Validation

# %%
def run_train_epoch() -> tuple[float, list[float], list[int], list[float]]:
    model.train()
    total_loss = 0.0
    dice_scores = np.zeros(NUM_CLASSES, dtype=np.float64)
    dice_counts = np.zeros(NUM_CLASSES, dtype=np.int64)
    positive_rates = np.zeros(NUM_CLASSES, dtype=np.float64)
    seen_batches = 0

    progress = tqdm(train_loader, desc="Train", leave=False)
    optimizer.zero_grad(set_to_none=True)
    for step, (images, masks) in enumerate(progress, start=1):
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)
        loss_targets = make_loss_targets(masks)

        with autocast("cuda", enabled=USE_AMP):
            logits = model(images)
            raw_loss = criterion(logits, loss_targets)
            loss = raw_loss / GRAD_ACCUM_STEPS

        scaler.scale(loss).backward()
        if step % GRAD_ACCUM_STEPS == 0 or step == len(train_loader):
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)

        batch_size = images.size(0)
        total_loss += raw_loss.item() * batch_size

        scores, counts = dice_by_class(logits.detach().float(), masks.detach())
        dice_scores += scores
        dice_counts += counts
        positive_rates += predicted_positive_rate(logits.detach().float())
        seen_batches += 1

        progress.set_postfix(loss=f"{raw_loss.item():.4f}")

    epoch_loss = total_loss / len(train_dataset)
    epoch_dice = divide_scores(dice_scores, dice_counts)
    epoch_positive_rates = (positive_rates / max(seen_batches, 1)).tolist()
    return epoch_loss, epoch_dice, dice_counts.tolist(), epoch_positive_rates


@torch.no_grad()
def run_valid_epoch() -> tuple[
    float,
    list[float],
    list[int],
    list[float],
    dict[str, dict[str, float]],
]:
    model.eval()
    total_loss = 0.0
    dice_scores = np.zeros(NUM_CLASSES, dtype=np.float64)
    dice_counts = np.zeros(NUM_CLASSES, dtype=np.int64)
    positive_rates = np.zeros(NUM_CLASSES, dtype=np.float64)
    seen_batches = 0
    threshold_score_sums = {
        threshold: np.zeros(NUM_CLASSES, dtype=np.float64)
        for threshold in EVAL_THRESHOLDS
    }
    threshold_count_sums = {
        threshold: np.zeros(NUM_CLASSES, dtype=np.int64)
        for threshold in EVAL_THRESHOLDS
    }

    progress = tqdm(valid_loader, desc="Valid", leave=False)
    for images, masks in progress:
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)
        loss_targets = make_loss_targets(masks)

        with autocast("cuda", enabled=USE_AMP):
            logits = model(images)
            loss = criterion(logits, loss_targets)

        batch_size = images.size(0)
        total_loss += loss.item() * batch_size

        scores, counts = dice_by_class(logits.float(), masks)
        dice_scores += scores
        dice_counts += counts
        for threshold in EVAL_THRESHOLDS:
            threshold_scores, threshold_counts = dice_by_class(
                logits.float(),
                masks,
                threshold=threshold,
            )
            threshold_score_sums[threshold] += threshold_scores
            threshold_count_sums[threshold] += threshold_counts
        positive_rates += predicted_positive_rate(logits.float())
        seen_batches += 1

        progress.set_postfix(loss=f"{loss.item():.4f}")

    epoch_loss = total_loss / len(valid_dataset)
    epoch_dice = divide_scores(dice_scores, dice_counts)
    epoch_positive_rates = (positive_rates / max(seen_batches, 1)).tolist()
    best_thresholds = best_threshold_summary(threshold_score_sums, threshold_count_sums)
    return epoch_loss, epoch_dice, dice_counts.tolist(), epoch_positive_rates, best_thresholds


history: list[dict[str, object]] = []
best_val_loss = float("inf")
best_loss_epoch = 0
best_mean_dice = -1.0
best_dice_epoch = 0
best_thresholds_by_dice: dict[str, dict[str, float]] = {}
early_stop_counter = 0
start_time = time.time()

print("=" * 72)
print("Starting Attention UNet training")
print("=" * 72)

for epoch in range(1, EPOCHS + 1):
    epoch_start = time.time()
    train_loss, train_dice, train_dice_counts, train_positive_rates = run_train_epoch()
    (
        val_loss,
        val_dice,
        val_dice_counts,
        val_positive_rates,
        val_best_thresholds,
    ) = run_valid_epoch()

    best_threshold_dice_values = [
        float(val_best_thresholds[lesion]["dice"])
        for lesion in LESION_CLASSES
    ]
    best_mean_dice_for_epoch = float(np.mean(best_threshold_dice_values))

    current_lr = optimizer.param_groups[0]["lr"]
    scheduler.step(best_mean_dice_for_epoch)

    epoch_record = {
        "epoch": epoch,
        "image_size": IMAGE_SIZE,
        "batch_size": BATCH_SIZE,
        "grad_accum_steps": GRAD_ACCUM_STEPS,
        "effective_batch_size": BATCH_SIZE * GRAD_ACCUM_STEPS,
        "class_weight_multiplier": {
            cls: float(CLASS_WEIGHT_MULTIPLIER[i])
            for i, cls in enumerate(LESION_CLASSES)
        },
        "loss_mask_dilation": LOSS_MASK_DILATION,
        "train_loss": float(train_loss),
        "val_loss": float(val_loss),
        "train_dice": {cls: float(train_dice[i]) for i, cls in enumerate(LESION_CLASSES)},
        "val_dice": {cls: float(val_dice[i]) for i, cls in enumerate(LESION_CLASSES)},
        "train_pred_positive_rate": {
            cls: float(train_positive_rates[i]) for i, cls in enumerate(LESION_CLASSES)
        },
        "val_pred_positive_rate": {
            cls: float(val_positive_rates[i]) for i, cls in enumerate(LESION_CLASSES)
        },
        "val_best_thresholds": val_best_thresholds,
        "val_best_mean_dice": best_mean_dice_for_epoch,
        "train_dice_valid_samples": {
            cls: int(train_dice_counts[i]) for i, cls in enumerate(LESION_CLASSES)
        },
        "val_dice_valid_samples": {
            cls: int(val_dice_counts[i]) for i, cls in enumerate(LESION_CLASSES)
        },
        "lr": float(current_lr),
        "seconds": float(time.time() - epoch_start),
    }
    history.append(epoch_record)

    print(f"\nEpoch {epoch:03d}/{EPOCHS}")
    print(f"  Train loss: {train_loss:.6f}")
    print(f"  Val loss:   {val_loss:.6f}")
    print(f"  Best mean Dice over thresholds: {best_mean_dice_for_epoch:.4f}")
    print(f"  LR:         {current_lr:.2e}")
    print("  Val Dice by class:")
    for index, lesion in enumerate(LESION_CLASSES):
        print(
            f"    {lesion}: {val_dice[index]:.4f} "
            f"(valid GT samples: {val_dice_counts[index]}, "
            f"pred positive: {val_positive_rates[index] * 100:.4f}%, "
            f"best@{val_best_thresholds[lesion]['threshold']:.1f}: "
            f"{val_best_thresholds[lesion]['dice']:.4f})"
        )

    with open(HISTORY_PATH, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_loss_epoch = epoch
        torch.save(model.state_dict(), BEST_LOSS_MODEL_PATH)
        torch.save(model.state_dict(), MODEL_PATH)
        print(f"  Saved best-loss model -> {BEST_LOSS_MODEL_PATH}")
    else:
        print("  No val_loss improvement")

    if best_mean_dice_for_epoch > best_mean_dice:
        best_mean_dice = best_mean_dice_for_epoch
        best_dice_epoch = epoch
        best_thresholds_by_dice = val_best_thresholds
        early_stop_counter = 0
        torch.save(model.state_dict(), BEST_DICE_MODEL_PATH)
        print(f"  Saved best-dice model -> {BEST_DICE_MODEL_PATH}")
    else:
        early_stop_counter += 1
        print(f"  No best Dice improvement: {early_stop_counter}/{EARLY_STOP_PATIENCE}")

    if early_stop_counter >= EARLY_STOP_PATIENCE:
        print(f"Early stopping triggered at epoch {epoch}.")
        break

print("=" * 72)
print(f"Training finished in {(time.time() - start_time) / 60:.1f} minutes")
print(f"Best loss epoch: {best_loss_epoch}")
print(f"Best val_loss: {best_val_loss:.6f}")
print(f"Best Dice epoch: {best_dice_epoch}")
print(f"Best mean Dice over thresholds: {best_mean_dice:.4f}")
print("=" * 72)


# %% [markdown]
# ## Validation Visualization

# %%
def denormalize_image(image_tensor: torch.Tensor) -> np.ndarray:
    image = image_tensor.detach().cpu().permute(1, 2, 0).numpy()
    mean = np.array(IMAGENET_MEAN, dtype=np.float32)
    std = np.array(IMAGENET_STD, dtype=np.float32)
    image = image * std + mean
    return np.clip(image, 0.0, 1.0)


@torch.no_grad()
def save_validation_samples(
    model_path: Path,
    thresholds: dict[str, float],
    sample_count: int = 4,
) -> None:
    if not model_path.exists():
        raise FileNotFoundError(f"Best model not found: {model_path}")

    best_model = AttentionUNet(
        in_channels=3,
        out_channels=NUM_CLASSES,
        features=MODEL_FEATURES,
    ).to(device)
    best_model.load_state_dict(torch.load(model_path, map_location=device))
    best_model.eval()

    rng = random.Random(SEED)
    sample_indices = rng.sample(range(len(valid_dataset)), k=min(sample_count, len(valid_dataset)))

    fig, axes = plt.subplots(
        len(sample_indices),
        NUM_CLASSES + 1,
        figsize=(20, 4 * len(sample_indices)),
        squeeze=False,
    )

    for row, sample_index in enumerate(sample_indices):
        image, gt_mask = valid_dataset[sample_index]
        with autocast("cuda", enabled=USE_AMP):
            logits = best_model(image.unsqueeze(0).to(device))
        probabilities = torch.sigmoid(logits).squeeze(0).cpu().numpy()
        pred_mask = np.zeros_like(probabilities, dtype=np.uint8)
        for class_index, lesion in enumerate(LESION_CLASSES):
            threshold = thresholds.get(lesion, THRESHOLD)
            pred_mask[class_index] = (probabilities[class_index] > threshold).astype(np.uint8)
        image_display = denormalize_image(image)
        image_uint8 = (image_display * 255).astype(np.uint8)
        pred_mask = postprocess_multiclass_masks(
            pred_mask,
            image_uint8,
            lesion_classes=tuple(LESION_CLASSES),
        )

        axes[row, 0].imshow(image_display)
        axes[row, 0].set_title("Image")
        axes[row, 0].axis("off")

        for class_index, lesion in enumerate(LESION_CLASSES):
            gt = gt_mask[class_index].cpu().numpy().astype(np.uint8)
            pred = pred_mask[class_index]
            combined = np.concatenate([gt, pred], axis=1)

            axes[row, class_index + 1].imshow(combined, cmap="gray", vmin=0, vmax=1)
            axes[row, class_index + 1].set_title(
                f"{lesion}: GT | Pred @ {thresholds.get(lesion, THRESHOLD):.2f}"
            )
            axes[row, class_index + 1].axis("off")

    fig.suptitle("Validation Samples: original image and lesion masks", fontsize=16)
    plt.tight_layout()
    plt.savefig(SAMPLES_PATH, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved validation samples -> {SAMPLES_PATH}")


recommended_thresholds = {
    lesion: float(best_thresholds_by_dice.get(lesion, {}).get("threshold", THRESHOLD))
    for lesion in LESION_CLASSES
}
if not best_thresholds_by_dice and history:
    best_thresholds_by_dice = history[-1]["val_best_thresholds"]
    recommended_thresholds = {
        lesion: float(best_thresholds_by_dice[lesion]["threshold"])
        for lesion in LESION_CLASSES
    }
with open(THRESHOLDS_PATH, "w", encoding="utf-8") as file:
    json.dump(
        {
            "thresholds": recommended_thresholds,
            "best_dice_epoch": best_dice_epoch,
            "best_mean_dice": best_mean_dice,
            "per_class": best_thresholds_by_dice,
        },
        file,
        indent=2,
    )
print(f"Saved recommended thresholds -> {THRESHOLDS_PATH}")

sample_model_path = BEST_DICE_MODEL_PATH if BEST_DICE_MODEL_PATH.exists() else MODEL_PATH
save_validation_samples(
    model_path=sample_model_path,
    thresholds=recommended_thresholds,
    sample_count=4,
)


# %% [markdown]
# ## Final Summary

# %%
if "history" not in globals() or not history:
    raise RuntimeError(
        "No training history found. Run the training cells first, "
        "or use Kaggle 'Restart Session and Run All'."
    )

best_loss_record = next(
    (record for record in history if record["epoch"] == best_loss_epoch),
    history[-1],
)
best_dice_record = next(
    (record for record in history if record["epoch"] == best_dice_epoch),
    history[-1],
)

print("\n" + "=" * 72)
print("Final training summary")
print("=" * 72)
print(f"Compatible best-loss state_dict: {MODEL_PATH}")
print(f"Best-loss state_dict: {BEST_LOSS_MODEL_PATH}")
print(f"Best-dice state_dict: {BEST_DICE_MODEL_PATH}")
print(f"Training history: {HISTORY_PATH}")
print(f"Recommended thresholds: {THRESHOLDS_PATH}")
print(f"Validation samples: {SAMPLES_PATH}")
print(f"Best loss epoch: {best_loss_epoch}")
print(f"Best val_loss: {best_val_loss:.6f}")
print(f"Best Dice epoch: {best_dice_epoch}")
print(f"Best mean Dice over thresholds: {best_mean_dice:.4f}")
print("\nRecommended thresholds:")
for lesion in LESION_CLASSES:
    print(f"  {lesion}: {recommended_thresholds[lesion]:.2f}")
print("\nBest-dice epoch val Dice by class:")
for lesion in LESION_CLASSES:
    dice_05 = best_dice_record["val_dice"][lesion]
    dice_best = best_dice_record["val_best_thresholds"][lesion]["dice"]
    threshold = best_dice_record["val_best_thresholds"][lesion]["threshold"]
    valid_samples = best_dice_record["val_dice_valid_samples"][lesion]
    print(
        f"  {lesion}: dice@0.50={dice_05:.4f}, "
        f"best@{threshold:.2f}={dice_best:.4f} "
        f"(valid GT samples: {valid_samples})"
    )
print("=" * 72)
