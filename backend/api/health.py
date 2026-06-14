from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from extensions import db


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    db_ok = True
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    model_path = Path(current_app.config["MODEL_PATH"])
    model_loaded = model_path.exists() and current_app.config["MODEL_BACKEND"] in {"auto", "real"}

    return jsonify(
        {
            "status": "ok" if db_ok else "degraded",
            "db": db_ok,
            "model_backend": current_app.config["MODEL_BACKEND"],
            "model_loaded": model_loaded,
            "model": "AttentionUNet" if model_loaded else None,
            "segmentation_classes": current_app.config["SEGMENTATION_CLASSES"],
        }
    )
