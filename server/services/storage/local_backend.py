from pathlib import Path

from config import settings


class LocalAvatarStorage:
    def upload(self, *, key: str, content: bytes, content_type: str) -> str:
        del content_type
        relative = key if key.startswith("/") else f"/{key}"
        if not relative.startswith("/uploads/"):
            relative = f"/uploads/{key.lstrip('/')}"

        target = Path(settings.upload_dir) / relative.removeprefix("/uploads/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return relative
