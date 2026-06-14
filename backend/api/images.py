from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, send_file

from errors import AppError
from services.auth_service import login_required
from services.image_service import ImageService


images_bp = Blueprint("images", __name__, url_prefix="/images")


@images_bp.get("/<path:image_path>")
@login_required
def get_image(image_path: str):
    try:
        absolute_path = ImageService.resolve_served_path(image_path, Path(current_app.root_path))
    except FileNotFoundError as exc:
        raise AppError("IMAGE_NOT_FOUND", "图片不存在", 404) from exc
    return send_file(absolute_path)
