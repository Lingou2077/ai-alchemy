from config import settings
from services.storage.base import AvatarStorage
from services.storage.cos_backend import CosAvatarStorage
from services.storage.local_backend import LocalAvatarStorage


def get_avatar_storage() -> AvatarStorage:
    if settings.avatar_storage == "cos":
        return CosAvatarStorage()
    return LocalAvatarStorage()


__all__ = ["AvatarStorage", "CosAvatarStorage", "LocalAvatarStorage", "get_avatar_storage"]
