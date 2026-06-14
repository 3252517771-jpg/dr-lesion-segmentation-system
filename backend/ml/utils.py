from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from PIL import Image


LESION_CLASSES = ("HE", "EX", "MA", "SE")
LESION_COLORS = {
    "HE": (255, 0, 0),
    "EX": (255, 255, 0),
    "MA": (0, 255, 0),
    "SE": (0, 0, 255),
}


@dataclass(frozen=True)
class PostprocessConfig:
    min_component_area: dict[str, int]
    keep_largest_components: dict[str, int | None]
    fundus_margin_ratio: float = 0.04
    fundus_threshold: int = 12
    morph_open_kernel: dict[str, int] | None = None


DEFAULT_POSTPROCESS_CONFIG = PostprocessConfig(
    min_component_area={"HE": 10, "EX": 12, "MA": 3, "SE": 16},
    keep_largest_components={"HE": 80, "EX": 80, "MA": 160, "SE": 50},
    morph_open_kernel={"HE": 0, "EX": 0, "MA": 0, "SE": 0},
)


def load_rgb_image(image_path: str | Path) -> np.ndarray:
    with Image.open(image_path) as image:
        return np.array(image.convert("RGB"))


def resize_image(image_rgb: np.ndarray, size: int) -> np.ndarray:
    return cv2.resize(image_rgb, (size, size), interpolation=cv2.INTER_AREA)


def build_fundus_roi(
    image_rgb: np.ndarray,
    config: PostprocessConfig = DEFAULT_POSTPROCESS_CONFIG,
) -> np.ndarray:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    roi = (gray > config.fundus_threshold).astype(np.uint8)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    roi = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, kernel)
    roi = cv2.morphologyEx(roi, cv2.MORPH_OPEN, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(roi, connectivity=8)
    if num_labels <= 1:
        return np.ones(gray.shape, dtype=np.uint8)

    largest_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    roi = (labels == largest_label).astype(np.uint8)

    height, width = roi.shape
    margin = max(1, int(min(height, width) * config.fundus_margin_ratio))
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (margin * 2 + 1, margin * 2 + 1))
    return cv2.erode(roi, erode_kernel, iterations=1).astype(np.uint8)


def filter_connected_components(mask: np.ndarray, min_area: int, keep_largest: int | None) -> np.ndarray:
    binary = (mask > 0).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        return binary

    components: list[tuple[int, int]] = []
    for label in range(1, num_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= min_area:
            components.append((label, area))

    if keep_largest is not None and len(components) > keep_largest:
        components = sorted(components, key=lambda item: item[1], reverse=True)[:keep_largest]

    output = np.zeros_like(binary)
    for label, _area in components:
        output[labels == label] = 1
    return output


def postprocess_multiclass_masks(
    masks: np.ndarray,
    image_rgb: np.ndarray,
    lesion_classes: tuple[str, ...] = LESION_CLASSES,
    config: PostprocessConfig = DEFAULT_POSTPROCESS_CONFIG,
) -> np.ndarray:
    if masks.ndim != 3:
        raise ValueError(f"Expected masks with shape [C,H,W], got {masks.shape}")

    roi = build_fundus_roi(image_rgb, config)
    processed = np.zeros_like(masks, dtype=np.uint8)

    for class_index, lesion in enumerate(lesion_classes):
        mask = (masks[class_index] > 0).astype(np.uint8) * roi
        kernel_size = (config.morph_open_kernel or {}).get(lesion, 0)
        if kernel_size and kernel_size > 1:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        processed[class_index] = filter_connected_components(
            mask,
            min_area=config.min_component_area.get(lesion, 1),
            keep_largest=config.keep_largest_components.get(lesion),
        )
    return processed


def resize_masks_to_original(masks: np.ndarray, original_size: tuple[int, int]) -> np.ndarray:
    width, height = original_size
    restored = []
    for mask in masks:
        resized = cv2.resize(mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST)
        restored.append((resized > 0).astype(np.uint8))
    return np.stack(restored, axis=0)


def compute_lesion_areas(
    masks: np.ndarray,
    image_shape: tuple[int, int],
    lesion_classes: tuple[str, ...] = LESION_CLASSES,
) -> dict[str, float]:
    height, width = image_shape
    total_pixels = max(height * width, 1)
    return {
        lesion: round(float(masks[index].sum()) / total_pixels * 100.0, 4)
        for index, lesion in enumerate(lesion_classes)
    }


def compute_lesion_counts(
    masks: np.ndarray,
    lesion_classes: tuple[str, ...] = LESION_CLASSES,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for index, lesion in enumerate(lesion_classes):
        binary = (masks[index] > 0).astype(np.uint8)
        num_labels, _labels = cv2.connectedComponents(binary, connectivity=8)
        counts[lesion] = max(num_labels - 1, 0)
    return counts


def estimate_severity(lesion_areas: dict[str, float], lesion_counts: dict[str, int] | None = None) -> str:
    lesion_counts = lesion_counts or {}
    if all(lesion_areas.get(lesion, 0.0) <= 0 for lesion in LESION_CLASSES):
        return "正常"
    if lesion_areas.get("HE", 0.0) >= 5.0 or lesion_areas.get("EX", 0.0) >= 5.0 or lesion_areas.get("SE", 0.0) >= 3.0:
        return "重度 NPDR"
    if lesion_areas.get("HE", 0.0) >= 1.0 or lesion_areas.get("EX", 0.0) >= 1.0:
        return "中度 NPDR"
    if lesion_counts.get("MA", 0) > 0 or all(lesion_areas.get(lesion, 0.0) < 1.0 for lesion in LESION_CLASSES):
        return "轻度 NPDR"
    return "正常"


def generate_contour_image(
    image_rgb: np.ndarray,
    masks: np.ndarray,
    output_dir: str | Path,
    lesion_classes: tuple[str, ...] = LESION_CLASSES,
    filename: str | None = None,
) -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    overlay = image_rgb.copy()
    for class_index, lesion in enumerate(lesion_classes):
        mask = (masks[class_index] > 0).astype(np.uint8)
        contours, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cv2.drawContours(overlay, contours, -1, LESION_COLORS[lesion], thickness=2)

    filename = filename or f"{uuid4().hex}.png"
    contour_path = output_path / filename
    Image.fromarray(overlay).save(contour_path)
    return str(contour_path)
