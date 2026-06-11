from qcloud_cos import CosConfig, CosS3Client

from config import settings


class CosAvatarStorage:
    def __init__(self) -> None:
        config = CosConfig(
            Region=settings.cos_region,
            SecretId=settings.cos_secret_id,
            SecretKey=settings.cos_secret_key,
        )
        self._client = CosS3Client(config)

    def upload(self, *, key: str, content: bytes, content_type: str) -> str:
        normalized_key = key.lstrip("/")
        self._client.put_object(
            Bucket=settings.cos_bucket,
            Key=normalized_key,
            Body=content,
            ContentType=content_type,
        )
        return self.build_public_url(normalized_key)

    def build_public_url(self, key: str) -> str:
        normalized_key = key.lstrip("/")
        base = settings.cos_public_base_url.strip().rstrip("/")
        if not base:
            base = f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com"
        return f"{base}/{normalized_key}"
