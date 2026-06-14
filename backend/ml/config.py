from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.getenv("MODEL_PATH", BACKEND_DIR / "trained_models" / "attention_unet_dr.pth"))
THRESHOLDS_PATH = Path(
    os.getenv("THRESHOLDS_PATH", BACKEND_DIR / "trained_models" / "recommended_thresholds.json")
)
INPUT_SIZE = int(os.getenv("INPUT_SIZE", "512"))
LESION_CLASSES = ("HE", "EX", "MA", "SE")
MODEL_FEATURES = (32, 64, 128, 256)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


@dataclass(frozen=True)
class ModelConfig:
    model_path: Path = MODEL_PATH
    thresholds_path: Path = THRESHOLDS_PATH
    input_size: int = INPUT_SIZE
    lesion_classes: tuple[str, ...] = LESION_CLASSES
    model_features: tuple[int, int, int, int] = MODEL_FEATURES
    imagenet_mean: tuple[float, float, float] = IMAGENET_MEAN
    imagenet_std: tuple[float, float, float] = IMAGENET_STD


def load_thresholds(config: ModelConfig = ModelConfig()) -> dict[str, float]:
    thresholds = {lesion: 0.5 for lesion in config.lesion_classes}
    if not config.thresholds_path.exists():
        return thresholds

    payload = json.loads(config.thresholds_path.read_text(encoding="utf-8"))
    loaded = payload.get("thresholds", payload)
    for lesion in config.lesion_classes:
        if lesion in loaded:
            thresholds[lesion] = float(loaded[lesion])
    return thresholds
