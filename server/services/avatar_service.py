import uuid
from pathlib import Path

from fastapi import UploadFile

from config import settings
from services.storage import get_avatar_storage

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024

CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _avatar_dir() -> Path:
    path = Path(settings.upload_dir) / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_extension(filename: str) -> str:
    ext = Path(filename.lower()).suffix
    if ext not in ALLOWED_EXTENSIONS:
        return ".jpg"
    return ext


def _build_object_key(user_id: int, filename: str) -> str:
    if settings.avatar_storage == "cos":
        prefix = settings.cos_avatar_prefix.strip().strip("/")
        return f"{prefix}/{filename}"
    return f"avatars/{filename}"


def save_avatar_file(user_id: int, file: UploadFile) -> str:
    original = (file.filename or "avatar.jpg").lower()
    ext = _resolve_extension(original)
    filename = f"{user_id}_{uuid.uuid4().hex}{ext}"

    content = file.file.read()
    if not content:
        raise ValueError("头像文件为空")
    if len(content) > MAX_AVATAR_BYTES:
        raise ValueError("头像文件过大，请小于 2MB")

    object_key = _build_object_key(user_id, filename)
    storage = get_avatar_storage()
    uploaded = storage.upload(
        key=object_key,
        content=content,
        content_type=CONTENT_TYPES[ext],
    )

    if uploaded.startswith(("http://", "https://")):
        return uploaded
    return build_public_avatar_url(uploaded, settings.public_base_url)


def build_public_avatar_url(relative_path: str, base_url: str) -> str:
    cleaned = relative_path.strip()
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return f"{base_url.rstrip('/')}{cleaned}"
