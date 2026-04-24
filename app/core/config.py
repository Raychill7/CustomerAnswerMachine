from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ecom-cs-agent"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_allow_origins: str = "*"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: int = 30
    deepseek_max_retries: int = 2

    postgres_dsn: str = "sqlite:///./data/app.db"
    redis_dsn: str = "redis://localhost:6379/0"
    chroma_dir: str = "./data/chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
