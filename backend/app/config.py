from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/yaqidh"
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CLIP_RETENTION_DAYS: int = 30
    CLIP_RETENTION_CHECK_INTERVAL: int = 86400
    MODEL_DIR: str = "models"
    CLIPS_DIR: str = "incident_clips"
    FALL_CONFIDENCE_THRESHOLD: float = 0.55  
    VIOLENCE_CONFIDENCE_THRESHOLD: float = 0.75
    PORT: int = 8000
    OTP_EXPIRE_MINUTES: int = 10
    ECHO_SQL: bool = False

    # --- SECURE ENVIRONMENT BINDINGS ---
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SENDER_EMAIL: Optional[str] = None
    MANAGER_TEST_EMAIL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()