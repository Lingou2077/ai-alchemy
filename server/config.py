from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    cors_origins: str = "*"
    content_max_length: int = 5000
    content_truncate_length: int = 4000
    ai_timeout_seconds: int = 60

    database_url: str = ""
    jwt_secret: str = "change-me"
    jwt_expire_seconds: int = 604800
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    dev_mock_login: bool = True
    upload_dir: str = "uploads"
    public_base_url: str = "http://127.0.0.1:8000"

    tavily_api_key: str = ""
    tavily_mock: bool = False
    research_agent_max_tool_calls: int = 4
    research_agent_timeout_seconds: int = 45
    tavily_search_max_results: int = 8
    tavily_search_default_depth: str = "advanced"
    research_session_ttl_seconds: int = 1800
    generation_task_ttl_seconds: int = 3600

    search_content_max: int = 2000
    extract_content_max: int = 4500
    materials_max_count: int = 20
    topic_candidate_materials_budget: int = 7000
    grounding_budget: int = 4500
    agent_tool_content_preview_chars: int = 600
    agent_tool_message_max_chars: int = 5000


settings = Settings()
