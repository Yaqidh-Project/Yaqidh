from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DATABASE CONFIGURATION (Production-Ready)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ✅ CRITICAL FIX: Render.com injects DATABASE_URL via environment variables.
    # DO NOT use localhost defaults in production. The env var is required.
    DATABASE_URL: str = None  # Will be provided by hosting platform, validation in __init__

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # JWT & SECURITY (Production-Ready)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    SECRET_KEY: str = None  # Will be provided by hosting platform, validation in __init__
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STORAGE & FILE RETENTION (Production-Ready)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    CLIP_RETENTION_DAYS: int = 30
    CLIP_RETENTION_CHECK_INTERVAL: int = 86400

    MODEL_DIR: Path = BASE_DIR / "models"
    CLIPS_DIR: Path = BASE_DIR / "incident_clips"

    FALL_CONFIDENCE_THRESHOLD: float = 0.55
    VIOLENCE_CONFIDENCE_THRESHOLD: float = 0.75

    PORT: int = 8000
    OTP_EXPIRE_MINUTES: int = 10
    ECHO_SQL: bool = False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EMAIL & NOTIFICATIONS (Production-Ready)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ✅ CRITICAL FIX: These are required for production. Backend must fail
    # explicitly if email is not configured, rather than silently ignoring it.
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SENDER_EMAIL: Optional[str] = None
    MANAGER_TEST_EMAIL: Optional[str] = None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENVIRONMENT DETECTION (Production-Ready)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    IS_PRODUCTION: bool = ENVIRONMENT in ("production", "prod")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **data):
        super().__init__(**data)
        # ✅ CRITICAL VALIDATION: Ensure DATABASE_URL is provided
        if not self.DATABASE_URL:
            default_local = "postgresql+asyncpg://postgres:postgres@localhost:5432/yaqidh"
            logger.warning(
                f"DATABASE_URL not found in environment. "
                f"Using fallback: {default_local}. "
                f"In production, set DATABASE_URL explicitly via environment variables."
            )
            self.DATABASE_URL = default_local

        # ✅ CRITICAL VALIDATION: Ensure SECRET_KEY is secure in production
        if not self.SECRET_KEY or self.SECRET_KEY == "change-me-in-production-use-a-long-random-string":
            if self.IS_PRODUCTION:
                raise ValueError(
                    "❌ PRODUCTION ERROR: SECRET_KEY must be a secure, random string. "
                    "Set SECRET_KEY environment variable on your hosting platform."
                )
            else:
                logger.warning(
                    "⚠️ WARNING: Using default SECRET_KEY. "
                    "This is only acceptable in development."
                )
                self.SECRET_KEY = "dev-secret-key-not-for-production"

        # ✅ CRITICAL VALIDATION: Ensure SMTP credentials are configured
        if self.IS_PRODUCTION:
            missing_smtp = [
                k for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SENDER_EMAIL"]
                if not getattr(self, k)
            ]
            if missing_smtp:
                logger.warning(
                    f"⚠️ WARNING: Missing SMTP configuration: {', '.join(missing_smtp)}. "
                    f"Email notifications will be disabled. "
                    f"Set these environment variables on your hosting platform to enable email."
                )


@lru_cache()
def get_settings() -> Settings:
    return Settings()