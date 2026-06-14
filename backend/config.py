from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    APP_NAME = os.getenv("APP_NAME", "DR Lesion Segmentation")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'retina_seg.db').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MODEL_BACKEND = os.getenv("MODEL_BACKEND", "auto")
    MODEL_PATH = os.getenv(
        "MODEL_PATH",
        str(BASE_DIR / "trained_models" / "attention_unet_dr.pth"),
    )
    INPUT_SIZE = int(os.getenv("INPUT_SIZE", "512"))
    SEGMENTATION_CLASSES = ["HE", "EX", "MA", "SE"]

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads" / "originals"))
    CONTOUR_FOLDER = os.getenv("CONTOUR_FOLDER", str(BASE_DIR / "uploads" / "contours"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_IMAGE_SIZE", str(10 * 1024 * 1024)))
    ALLOWED_EXTENSIONS = {
        item.strip().lower()
        for item in os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,bmp,webp").split(",")
        if item.strip()
    }


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
