from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app, init_runtime_database
from database.models import Diagnosis, Patient, User
from extensions import db
from services.diagnosis_service import DiagnosisService
from services.patient_service import PatientService
from services.user_service import UserService


DEMO_PATIENTS = [
    {
        "name": "Li Ming",
        "gender": "male",
        "age": 58,
        "patient_id": "DEMO-P001",
        "username": "patient_li",
        "password": "patient123",
        "severity": "轻度 NPDR",
        "lesion_areas": {"HE": 0.8, "EX": 0.3, "MA": 0.2, "SE": 0.0},
        "lesion_counts": {"HE": 5, "EX": 2, "MA": 18, "SE": 0},
    },
    {
        "name": "Wang Fang",
        "gender": "female",
        "age": 63,
        "patient_id": "DEMO-P002",
        "username": "patient_wang",
        "password": "patient123",
        "severity": "中度 NPDR",
        "lesion_areas": {"HE": 2.1, "EX": 1.4, "MA": 0.5, "SE": 0.4},
        "lesion_counts": {"HE": 12, "EX": 6, "MA": 31, "SE": 2},
    },
    {
        "name": "Zhang Wei",
        "gender": "male",
        "age": 69,
        "patient_id": "DEMO-P003",
        "username": "patient_zhang",
        "password": "patient123",
        "severity": "重度 NPDR",
        "lesion_areas": {"HE": 5.7, "EX": 3.2, "MA": 0.9, "SE": 3.4},
        "lesion_counts": {"HE": 28, "EX": 14, "MA": 48, "SE": 7},
    },
]

LESION_BOXES = {
    "HE": [(0.22, 0.28, 0.34, 0.40), (0.48, 0.44, 0.56, 0.54)],
    "EX": [(0.62, 0.26, 0.75, 0.38), (0.58, 0.60, 0.70, 0.70)],
    "MA": [(0.40, 0.58, 0.45, 0.63), (0.51, 0.34, 0.55, 0.38), (0.36, 0.42, 0.40, 0.46)],
    "SE": [(0.64, 0.52, 0.78, 0.66)],
}

LESION_COLORS = {
    "HE": (255, 77, 79),
    "EX": (212, 161, 6),
    "MA": (82, 196, 26),
    "SE": (22, 119, 255),
}


def make_demo_image(patient_id: str, output_dir: Path, index: int) -> tuple[str, str, dict[str, list[dict]]]:
    output_originals = output_dir / "uploads" / "originals"
    output_contours = output_dir / "uploads" / "contours"
    output_originals.mkdir(parents=True, exist_ok=True)
    output_contours.mkdir(parents=True, exist_ok=True)

    width = height = 512
    image = Image.new("RGB", (width, height), (12, 18, 26))
    draw = ImageDraw.Draw(image)
    draw.ellipse((46, 38, 466, 474), fill=(96 + index * 12, 46, 36), outline=(188, 110, 80), width=4)
    draw.ellipse((160, 150, 360, 350), fill=(128, 64, 44))
    draw.ellipse((350, 210, 420, 285), fill=(231, 204, 134))

    contour = image.copy()
    contour_draw = ImageDraw.Draw(contour)
    positions: dict[str, list[dict]] = {}
    for lesion, boxes in LESION_BOXES.items():
        positions[lesion] = []
        color = LESION_COLORS[lesion]
        for box in boxes[: max(1, min(len(boxes), index + 1))]:
            x1, y1, x2, y2 = box
            bounds = (int(x1 * width), int(y1 * height), int(x2 * width), int(y2 * height))
            contour_draw.rectangle(bounds, outline=color, width=3)
            area = max((bounds[2] - bounds[0]) * (bounds[3] - bounds[1]), 1)
            positions[lesion].append(
                {
                    "x": round((bounds[0] + bounds[2]) / 2 / width, 6),
                    "y": round((bounds[1] + bounds[3]) / 2 / height, 6),
                    "area": area,
                    "area_ratio": round(area / (width * height) * 100.0, 6),
                    "bbox": [bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1]],
                }
            )

    original_name = f"{patient_id.lower()}_fundus.jpg"
    contour_name = f"{patient_id.lower()}_contour.png"
    image.save(output_originals / original_name)
    contour.save(output_contours / contour_name)
    return f"uploads/originals/{original_name}", f"uploads/contours/{contour_name}", positions


def clear_demo_data() -> None:
    demo_patient_ids = [patient["patient_id"] for patient in DEMO_PATIENTS]
    demo_usernames = [patient["username"] for patient in DEMO_PATIENTS] + ["doctor_demo"]
    patient_primary_keys = [
        patient.id
        for patient in Patient.query.filter(Patient.patient_id.in_(demo_patient_ids)).all()
    ]

    if patient_primary_keys:
        Diagnosis.query.filter(Diagnosis.patient_id.in_(patient_primary_keys)).delete(synchronize_session=False)
    User.query.filter(User.username.in_(demo_usernames)).delete(synchronize_session=False)
    Patient.query.filter(Patient.patient_id.in_(demo_patient_ids)).delete(synchronize_session=False)
    db.session.commit()


def seed_demo_data(reset: bool = False, app=None) -> None:
    flask_app = app or create_app()
    with flask_app.app_context():
        init_runtime_database(flask_app)
        if reset:
            clear_demo_data()

        UserService.ensure_default_admin(
            username="doctor_demo",
            password="doctor123",
            display_name="Demo Doctor",
        )

        for index, item in enumerate(DEMO_PATIENTS):
            patient = Patient.query.filter_by(patient_id=item["patient_id"], is_deleted=False).first()
            if not patient:
                patient = PatientService.create_patient(
                    {
                        "name": item["name"],
                        "gender": item["gender"],
                        "age": item["age"],
                        "patient_id": item["patient_id"],
                    }
                )

            user = User.query.filter_by(username=item["username"], is_deleted=False).first()
            if not user:
                UserService.create_user(
                    {
                        "username": item["username"],
                        "display_name": item["name"],
                        "password": item["password"],
                        "role": "patient",
                        "linked_patient_id": patient.id,
                    }
                )

            existing_diagnosis = Diagnosis.query.filter_by(patient_id=patient.id, is_deleted=False).first()
            if existing_diagnosis:
                continue

            image_path, contour_path, positions = make_demo_image(item["patient_id"], BACKEND_DIR, index)
            DiagnosisService.create_diagnosis(
                patient_id=patient.id,
                image_path=image_path,
                contour_path=contour_path,
                lesion_areas=item["lesion_areas"],
                lesion_counts=item["lesion_counts"],
                lesion_positions=positions,
                severity=item["severity"],
                notes="Demo seed record for presentation.",
            )

        print("Demo data seeded.")
        print("Doctor account: doctor_demo / doctor123")
        print("Patient accounts: patient_li, patient_wang, patient_zhang / patient123")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo users, patients, diagnoses, and images.")
    parser.add_argument("--reset", action="store_true", help="Delete existing demo records before seeding.")
    args = parser.parse_args()
    seed_demo_data(reset=args.reset)


if __name__ == "__main__":
    main()
