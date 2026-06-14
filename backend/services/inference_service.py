from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw
from flask import current_app
from werkzeug.datastructures import FileStorage

from errors import InferenceError, ModelLoadError, ValidationError
from ml.config import ModelConfig
from ml.inference import RealInference
from services.diagnosis_service import DiagnosisService
from services.image_service import ImageService
from services.patient_service import PatientService


class InferenceService:
    @staticmethod
    def run_diagnosis(file: FileStorage, patient_id: int) -> dict:
        PatientService.get_patient(patient_id)
        saved = ImageService.save_upload(
            file,
            current_app.config["UPLOAD_FOLDER"],
            current_app.config["ALLOWED_EXTENSIONS"],
        )
        result = InferenceService._run_inference(saved["absolute_path"])
        diagnosis = DiagnosisService.create_diagnosis(
            patient_id=patient_id,
            image_path=saved["relative_path"],
            contour_path=result["contour_path"],
            lesion_areas=result["lesion_areas"],
            lesion_counts=result["lesion_counts"],
            lesion_positions=result.get("lesion_positions", {}),
            severity=result["severity"],
        )
        return {"diagnosis": diagnosis.to_dict(), "mode": result["mode"]}

    @staticmethod
    def _run_inference(image_path: str) -> dict:
        mode = current_app.config["MODEL_BACKEND"]
        if mode not in {"auto", "real", "placeholder"}:
            raise ValidationError("MODEL_BACKEND 只能是 auto、real 或 placeholder")
        if mode == "placeholder":
            return InferenceService._run_placeholder(image_path)
        try:
            return InferenceService._run_real(image_path)
        except Exception as exc:
            if mode == "real":
                if isinstance(exc, FileNotFoundError):
                    raise ModelLoadError() from exc
                raise InferenceError(str(exc)) from exc
            return InferenceService._run_placeholder(image_path)

    @staticmethod
    def _run_real(image_path: str) -> dict:
        config = ModelConfig(
            model_path=Path(current_app.config["MODEL_PATH"]),
            input_size=int(current_app.config["INPUT_SIZE"]),
        )
        result = RealInference(config=config).predict(
            image_path,
            contour_dir=current_app.config["CONTOUR_FOLDER"],
        )
        contour_path = result["contour_path"]
        if contour_path:
            contour_path = ImageService.relative_to_backend(contour_path, Path(current_app.root_path))
        return {
            "lesion_areas": result["lesion_areas"],
            "lesion_counts": result["lesion_counts"],
            "lesion_positions": result.get("lesion_positions", {}),
            "severity": result["severity"],
            "contour_path": contour_path,
            "mode": "real",
        }

    @staticmethod
    def _run_placeholder(image_path: str) -> dict:
        contour_dir = Path(current_app.config["CONTOUR_FOLDER"])
        contour_dir.mkdir(parents=True, exist_ok=True)
        contour_path = contour_dir / f"{uuid4().hex}.png"

        try:
            with Image.open(image_path).convert("RGB") as image:
                overlay = image.copy()
        except Exception as exc:
            raise InferenceError("占位推理无法读取图片") from exc

        draw = ImageDraw.Draw(overlay)
        width, height = overlay.size
        boxes = [
            ("HE", "red", (0.22, 0.24, 0.34, 0.36)),
            ("EX", "yellow", (0.58, 0.32, 0.72, 0.44)),
            ("MA", "green", (0.42, 0.58, 0.50, 0.66)),
            ("SE", "blue", (0.62, 0.62, 0.78, 0.76)),
        ]
        for label, color, box in boxes:
            x1, y1, x2, y2 = box
            draw.rectangle(
                (x1 * width, y1 * height, x2 * width, y2 * height),
                outline=color,
                width=max(2, width // 180),
            )
            draw.text((x1 * width, y1 * height), label, fill=color)
        overlay.save(contour_path)

        return {
            "lesion_areas": {"HE": 1.8, "EX": 0.9, "MA": 0.3, "SE": 0.6},
            "lesion_counts": {"HE": 8, "EX": 4, "MA": 12, "SE": 2},
            "lesion_positions": {
                label: [
                    {
                        "x": round((box[0] + box[2]) / 2, 4),
                        "y": round((box[1] + box[3]) / 2, 4),
                        "area": int((box[2] - box[0]) * width * (box[3] - box[1]) * height),
                        "area_ratio": round((box[2] - box[0]) * (box[3] - box[1]) * 100, 4),
                        "bbox": [
                            int(box[0] * width),
                            int(box[1] * height),
                            int((box[2] - box[0]) * width),
                            int((box[3] - box[1]) * height),
                        ],
                    }
                ]
                for label, _color, box in boxes
            },
            "severity": "中度 NPDR",
            "contour_path": ImageService.relative_to_backend(contour_path, Path(current_app.root_path)),
            "mode": "placeholder",
        }
