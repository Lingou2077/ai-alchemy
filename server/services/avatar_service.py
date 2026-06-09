import uuid
from pathlib import Path

from fastapi import UploadFile

from config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


def _avatar_dir() -> Path:
    path = Path(settings.upload_dir) / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_avatar_file(user_id: int, file: UploadFile) -> str:
    original = (file.filename or "avatar.jpg").lower()
    ext = Path(original).suffix
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"

    filename = f"{user_id}_{uuid.uuid4().hex}{ext}"
    target = _avatar_dir() / filename
    content = file.file.read()
    if not content:
        raise ValueError("头像文件为空")
    if len(content) > MAX_AVATAR_BYTES:
        raise ValueError("头像文件过大，请小于 2MB")

    target.write_bytes(content)
    return f"/uploads/avatars/{filename}"


def build_public_avatar_url(relative_path: str, base_url: str) -> str:
    cleaned = relative_path.strip()
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return f"{base_url.rstrip('/')}{cleaned}"
