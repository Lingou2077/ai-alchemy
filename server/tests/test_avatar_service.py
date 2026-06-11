import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile

from services.avatar_service import build_public_avatar_url, save_avatar_file


def _upload_file(name: str, content: bytes) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(content))


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_save_avatar_file_local_mode_writes_uploads_path():
    with patch("services.avatar_service.settings") as mock_settings:
        mock_settings.avatar_storage = "local"
        mock_settings.cos_avatar_prefix = "aialchemy/avatars"
        mock_settings.public_base_url = "http://127.0.0.1:8000"
        mock_settings.upload_dir = "uploads"

        url = save_avatar_file(9, _upload_file("avatar.png", PNG_BYTES))

    assert url.startswith("http://127.0.0.1:8000/uploads/avatars/9_")
    assert url.endswith(".png")


def test_save_avatar_file_cos_mode_returns_https_url():
    mock_storage = MagicMock()
    mock_storage.upload.return_value = (
        "https://yunpic-1348558641.cos.ap-guangzhou.myqcloud.com/aialchemy/avatars/3_abc.png"
    )

    with (
        patch("services.avatar_service.settings") as mock_settings,
        patch("services.avatar_service.get_avatar_storage", return_value=mock_storage),
    ):
        mock_settings.avatar_storage = "cos"
        mock_settings.cos_avatar_prefix = "aialchemy/avatars"

        url = save_avatar_file(3, _upload_file("avatar.png", PNG_BYTES))

    mock_storage.upload.assert_called_once()
    upload_kwargs = mock_storage.upload.call_args.kwargs
    assert upload_kwargs["key"].startswith("aialchemy/avatars/3_")
    assert upload_kwargs["content_type"] == "image/png"
    assert url.startswith("https://")
    assert "/aialchemy/avatars/" in url


def test_save_avatar_file_rejects_empty_file():
    with pytest.raises(ValueError, match="头像文件为空"):
        save_avatar_file(1, _upload_file("avatar.png", b""))


def test_build_public_avatar_url_keeps_absolute_url():
    url = build_public_avatar_url(
        "https://yunpic-1348558641.cos.ap-guangzhou.myqcloud.com/aialchemy/avatars/1.png",
        "http://127.0.0.1:8000",
    )
    assert url.startswith("https://yunpic-1348558641.cos.ap-guangzhou.myqcloud.com")
