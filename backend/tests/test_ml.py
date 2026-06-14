from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml.config import ModelConfig, load_thresholds
from ml.inference import RealInference
from ml.model import AttentionUNet
from ml.utils import (
    compute_lesion_areas,
    compute_lesion_counts,
    estimate_severity,
    extract_lesion_positions,
    generate_contour_image,
    postprocess_multiclass_masks,
)


def test_attention_unet_output_shape():
    import torch

    model = AttentionUNet(features=(32, 64, 128, 256))
    model.eval()
    with torch.no_grad():
        output = model(torch.zeros(1, 3, 128, 128))

    assert output.shape == (1, 4, 128, 128)


def test_thresholds_load_from_runtime_file():
    thresholds = load_thresholds()

    assert thresholds == {"HE": 0.5, "EX": 0.5, "MA": 0.5, "SE": 0.5}


def test_postprocess_filters_noise_and_metrics(tmp_path):
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    image[16:112, 16:112] = 80
    masks = np.zeros((4, 128, 128), dtype=np.uint8)
    masks[0, 50:60, 50:60] = 1
    masks[0, 10, 10] = 1
    masks[1, 80:84, 80:84] = 1
    masks[2, 40:42, 40:42] = 1

    processed = postprocess_multiclass_masks(masks, image)
    assert processed[0, 55, 55] == 1
    assert processed[0, 10, 10] == 0
    assert processed[1].sum() >= 12

    areas = compute_lesion_areas(processed, image.shape[:2])
    counts = compute_lesion_counts(processed)
    positions = extract_lesion_positions(processed, image.shape[:2])
    assert areas["HE"] > 0
    assert counts["HE"] == 1
    assert len(positions["HE"]) == 1
    assert 0 < positions["HE"][0]["x"] < 1
    assert 0 < positions["HE"][0]["y"] < 1
    assert positions["HE"][0]["area"] > 0
    assert len(positions["HE"][0]["bbox"]) == 4
    assert estimate_severity({"HE": 0, "EX": 0, "MA": 0, "SE": 0}) == "正常"

    contour_path = generate_contour_image(image, processed, tmp_path, filename="contour.png")
    assert Path(contour_path).exists()


def test_real_model_loads_and_predicts_on_small_image(tmp_path):
    config = ModelConfig(input_size=128)
    inference = RealInference(config=config)
    model = inference.load_model()
    assert isinstance(model, AttentionUNet)

    image = np.zeros((160, 160, 3), dtype=np.uint8)
    image[..., 1] = 40
    image[30:130, 30:130, :] = [90, 70, 60]
    image_path = tmp_path / "fundus.jpg"
    Image.fromarray(image).save(image_path)

    result = inference.predict(image_path, contour_dir=tmp_path)

    assert set(result["lesion_areas"]) == {"HE", "EX", "MA", "SE"}
    assert set(result["lesion_counts"]) == {"HE", "EX", "MA", "SE"}
    assert set(result["lesion_positions"]) == {"HE", "EX", "MA", "SE"}
    assert result["masks"].shape == (4, 160, 160)
    assert Path(result["contour_path"]).exists()
