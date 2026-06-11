from unittest.mock import MagicMock, patch

import pytest

from services.storage.cos_backend import CosAvatarStorage


@pytest.fixture
def cos_settings():
    with patch("services.storage.cos_backend.settings") as mock_settings:
        mock_settings.cos_region = "ap-guangzhou"
        mock_settings.cos_secret_id = "test-id"
        mock_settings.cos_secret_key = "test-key"
        mock_settings.cos_bucket = "yunpic-1348558641"
        mock_settings.cos_public_base_url = "https://yunpic-1348558641.cos.ap-guangzhou.myqcloud.com"
        yield mock_settings


def test_cos_upload_uses_aialchemy_prefix(cos_settings):
    with patch("services.storage.cos_backend.CosS3Client") as client_cls:
        client = MagicMock()
        client_cls.return_value = client
        storage = CosAvatarStorage()

        url = storage.upload(
            key="aialchemy/avatars/1_abc.png",
            content=b"png",
            content_type="image/png",
        )

        client.put_object.assert_called_once_with(
            Bucket="yunpic-1348558641",
            Key="aialchemy/avatars/1_abc.png",
            Body=b"png",
            ContentType="image/png",
        )
        assert url == "https://yunpic-1348558641.cos.ap-guangzhou.myqcloud.com/aialchemy/avatars/1_abc.png"


def test_build_public_url_falls_back_to_default_domain(cos_settings):
    cos_settings.cos_public_base_url = ""
    with patch("services.storage.cos_backend.CosS3Client"):
        storage = CosAvatarStorage()
        url = storage.build_public_url("aialchemy/avatars/2_def.jpg")
        assert url == "https://yunpic-1348558641.cos.ap-guangzhou.myqcloud.com/aialchemy/avatars/2_def.jpg"
