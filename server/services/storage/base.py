from typing import Protocol


class AvatarStorage(Protocol):
    def upload(self, *, key: str, content: bytes, content_type: str) -> str:
        """上传头像并返回可公开访问的 URL。"""
