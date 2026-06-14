from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from ml.config import ModelConfig, load_thresholds
from ml.model import AttentionUNet
from ml.utils import (
    compute_lesion_areas,
    compute_lesion_counts,
    estimate_severity,
    extract_lesion_positions,
    generate_contour_image,
    load_rgb_image,
    postprocess_multiclass_masks,
    resize_image,
    resize_masks_to_original,
)


class RealInference:
    def __init__(self, config: ModelConfig = ModelConfig(), device: str | None = None) -> None:
        self.config = config
        self.device = torch.device(device or "cpu")
        self.thresholds = load_thresholds(config)
        self.model: AttentionUNet | None = None

    def load_model(self) -> AttentionUNet:
        if self.model is not None:
            return self.model
        if not self.config.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.config.model_path}")

        model = AttentionUNet(
            in_channels=3,
            out_channels=len(self.config.lesion_classes),
            features=self.config.model_features,
        )
        state_dict = torch.load(self.config.model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        self.model = model
        return model

    def preprocess(self, image_rgb: np.ndarray) -> torch.Tensor:
        resized = resize_image(image_rgb, self.config.input_size).astype(np.float32) / 255.0
        mean = np.array(self.config.imagenet_mean, dtype=np.float32)
        std = np.array(self.config.imagenet_std, dtype=np.float32)
        normalized = (resized - mean) / std
        tensor = torch.from_numpy(normalized.transpose(2, 0, 1)).float().unsqueeze(0)
        return tensor.to(self.device)

    @torch.no_grad()
    def predict_masks(self, image_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        model = self.load_model()
        inputs = self.preprocess(image_rgb)
        logits = model(inputs)
        probabilities = torch.sigmoid(logits).squeeze(0).cpu().numpy()
        thresholds = np.array(
            [self.thresholds[lesion] for lesion in self.config.lesion_classes],
            dtype=np.float32,
        )[:, None, None]
        masks = (probabilities >= thresholds).astype(np.uint8)
        return probabilities, masks

    def predict(self, image_path: str | Path, contour_dir: str | Path | None = None) -> dict:
        image_rgb = load_rgb_image(image_path)
        original_height, original_width = image_rgb.shape[:2]
        probabilities, resized_masks = self.predict_masks(image_rgb)
        processed_resized = postprocess_multiclass_masks(
            resized_masks,
            resize_image(image_rgb, self.config.input_size),
            lesion_classes=self.config.lesion_classes,
        )
        masks = resize_masks_to_original(processed_resized, (original_width, original_height))

        lesion_areas = compute_lesion_areas(masks, (original_height, original_width), self.config.lesion_classes)
        lesion_counts = compute_lesion_counts(masks, self.config.lesion_classes)
        lesion_positions = extract_lesion_positions(masks, (original_height, original_width), self.config.lesion_classes)
        severity = estimate_severity(lesion_areas, lesion_counts)
        contour_path = None
        if contour_dir is not None:
            contour_path = generate_contour_image(image_rgb, masks, contour_dir, self.config.lesion_classes)

        return {
            "lesion_areas": lesion_areas,
            "lesion_counts": lesion_counts,
            "lesion_positions": lesion_positions,
            "severity": severity,
            "contour_path": contour_path,
            "masks": masks,
            "probabilities": probabilities,
            "thresholds": self.thresholds,
        }


def predict(image_path: str | Path, contour_dir: str | Path | None = None) -> dict:
    return RealInference().predict(image_path, contour_dir=contour_dir)
