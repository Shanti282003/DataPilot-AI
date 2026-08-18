from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "DataPilot"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    MAX_UPLOAD_SIZE_MB: int = 100

    # Database
    DATABASE_URL: Optional[str] = "sqlite:///./datapilot_dev.db"

    # AI Service
    DEEPSEEK_API_KEY: str = "dummy_key_for_testing"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    AI_MODEL_NAME: str = "deepseek-chat"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Singleton instance
settings = Settings()