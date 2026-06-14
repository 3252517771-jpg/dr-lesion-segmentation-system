from __future__ import annotations

from pathlib import Path

import sys


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from database.models import Diagnosis, Patient, User
from seed import seed_demo_data


def test_seed_demo_data_creates_closed_loop(app):
    seed_demo_data(reset=True, app=app)

    patients = Patient.query.filter(Patient.patient_id.like("DEMO-P%")).all()
    patient_users = User.query.filter(User.username.like("patient_%")).all()
    doctor = User.query.filter_by(username="doctor_demo").first()
    diagnoses = Diagnosis.query.join(Patient).filter(Patient.patient_id.like("DEMO-P%")).all()

    assert len(patients) == 3
    assert len(patient_users) == 3
    assert doctor is not None
    assert doctor.role == "doctor"
    assert len(diagnoses) == 3
    assert all(diagnosis.image_path.startswith("uploads/originals/") for diagnosis in diagnoses)
    assert all(diagnosis.contour_path.startswith("uploads/contours/") for diagnosis in diagnoses)
    assert all(diagnosis.lesion_positions["HE"] for diagnosis in diagnoses)
