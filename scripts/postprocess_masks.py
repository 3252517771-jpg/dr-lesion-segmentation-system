from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


LESION_CLASSES = ("HE", "EX", "MA", "SE")


@dataclass(frozen=True)
class PostprocessConfig:
    min_component_area: dict[str, int]
    keep_largest_components: dict[str, int | None]
    fundus_margin_ratio: float = 0.04
    fundus_threshold: int = 12
    morph_open_kernel: dict[str, int] | None = None


DEFAULT_POSTPROCESS_CONFIG = PostprocessConfig(
    min_component_area={
        "HE": 10,
        "EX": 12,
        "MA": 3,
        "SE": 16,
    },
    keep_largest_components={
        "HE": 80,
        "EX": 80,
        "MA": 160,
        "SE": 50,
    },
    morph_open_kernel={
        "HE": 0,
        "EX": 0,
        "MA": 0,
        "SE": 0,
    },
)


def build_fundus_roi(image_rgb: np.ndarray, config: PostprocessConfig = DEFAULT_POSTPROCESS_CONFIG) -> np.ndarray:
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
    erode_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (margin * 2 + 1, margin * 2 + 1),
    )
    roi = cv2.erode(roi, erode_kernel, iterations=1)
    return roi.astype(np.uint8)


def filter_connected_components(
    mask: np.ndarray,
    min_area: int,
    keep_largest: int | None,
) -> np.ndarray:
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
    for label, _ in components:
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
        mask = (masks[class_index] > 0).astype(np.uint8)
        mask = mask * roi

        kernel_size = (config.morph_open_kernel or {}).get(lesion, 0)
        if kernel_size and kernel_size > 1:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (kernel_size, kernel_size),
            )
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        processed[class_index] = filter_connected_components(
            mask,
            min_area=config.min_component_area.get(lesion, 1),
            keep_largest=config.keep_largest_components.get(lesion),
        )

    return processed
