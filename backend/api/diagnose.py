from __future__ import annotations

from flask import Blueprint, jsonify, request

from errors import ValidationError
from services.auth_service import doctor_required
from services.inference_service import InferenceService


diagnose_bp = Blueprint("diagnose", __name__)


@diagnose_bp.post("/diagnose")
@doctor_required
def diagnose():
    if "image" not in request.files:
        raise ValidationError("请上传眼底图片")
    patient_id_raw = request.form.get("patient_id")
    if not patient_id_raw:
        raise ValidationError("患者 ID 不能为空")
    try:
        patient_id = int(patient_id_raw)
    except ValueError as exc:
        raise ValidationError("患者 ID 必须是整数") from exc

    result = InferenceService.run_diagnosis(request.files["image"], patient_id)
    return jsonify(result), 201
