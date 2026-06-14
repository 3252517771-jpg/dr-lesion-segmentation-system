from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from errors import InvalidImageError


class ImageService:
    @staticmethod
    def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions

    @staticmethod
    def save_upload(file: FileStorage, upload_folder: str, allowed_extensions: set[str]) -> dict:
        if not file or not file.filename:
            raise InvalidImageError("请上传眼底图片")
        if not ImageService.allowed_file(file.filename, allowed_extensions):
            raise InvalidImageError("仅支持 jpg/jpeg/png/bmp/webp 格式")

        original_name = secure_filename(file.filename)
        suffix = Path(original_name).suffix.lower()
        filename = f"{uuid4().hex}{suffix}"
        upload_dir = Path(upload_folder)
        upload_dir.mkdir(parents=True, exist_ok=True)
        absolute_path = upload_dir / filename
        file.save(absolute_path)

        try:
            with Image.open(absolute_path) as image:
                image.verify()
        except Exception as exc:
            absolute_path.unlink(missing_ok=True)
            raise InvalidImageError("图片文件无法读取") from exc

        return {
            "absolute_path": str(absolute_path),
            "relative_path": f"uploads/originals/{filename}",
            "filename": filename,
        }

    @staticmethod
    def relative_to_backend(path: str | Path, backend_dir: str | Path) -> str:
        absolute = Path(path).resolve()
        backend = Path(backend_dir).resolve()
        return absolute.relative_to(backend).as_posix()

    @staticmethod
    def resolve_served_path(image_path: str, backend_dir: str | Path) -> Path:
        normalized = image_path.replace("\\", "/").lstrip("/")
        if normalized.startswith("api/images/"):
            normalized = normalized.removeprefix("api/images/")
        absolute = (Path(backend_dir) / normalized).resolve()
        backend = Path(backend_dir).resolve()
        if backend not in absolute.parents and absolute != backend:
            raise InvalidImageError("图片路径不合法")
        if not absolute.exists() or not absolute.is_file():
            raise FileNotFoundError(normalized)
        return absolute
