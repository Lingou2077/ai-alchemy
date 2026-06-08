from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    cors_origins: str = "*"
    content_max_length: int = 5000
    content_truncate_length: int = 4000
    ai_timeout_seconds: int = 30

    database_url: str = ""
    jwt_secret: str = "change-me"
    jwt_expire_seconds: int = 604800
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    dev_mock_login: bool = True


settings = Settings()
