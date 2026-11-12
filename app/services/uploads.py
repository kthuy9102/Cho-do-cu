"""Lưu ảnh upload an toàn: kiểm tra content-type, kích thước và CHỮ KÝ FILE (magic bytes);
tên file do server sinh ngẫu nhiên, không bao giờ dùng tên client gửi lên (chống path traversal)."""
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.core.exceptions import BadRequestError, PayloadTooLargeError, UnsupportedMediaTypeError

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _detect_extension(head: bytes) -> str | None:
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def save_image(file: UploadFile, subdir: str) -> str:
    """Lưu ảnh, trả về đường dẫn tương đối so với UPLOAD_DIR."""
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError("Chỉ chấp nhận ảnh JPEG, PNG hoặc WebP", code="invalid_image_type")

    data = file.file.read(max_bytes + 1)
    if not data:
        raise BadRequestError("Tệp ảnh rỗng", code="empty_file")
    if len(data) > max_bytes:
        raise PayloadTooLargeError(
            f"Ảnh vượt quá dung lượng tối đa {settings.max_upload_size_mb} MB", code="image_too_large"
        )

    ext = _detect_extension(data[:12])
    if ext is None:  # content-type có thể bị giả; nội dung mới là sự thật
        raise UnsupportedMediaTypeError("Nội dung tệp không phải ảnh hợp lệ", code="invalid_image_content")

    relative = f"{subdir}/{uuid.uuid4().hex}.{ext}"
    destination = Path(settings.upload_dir) / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return relative


def delete_file(relative_path: str) -> None:
    base = Path(get_settings().upload_dir).resolve()
    target = (base / relative_path).resolve()
    if base in target.parents and target.is_file():  # không xóa được file ngoài thư mục upload
        target.unlink(missing_ok=True)
