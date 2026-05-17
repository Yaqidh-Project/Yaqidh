from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt  # type: ignore
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    try:
        payload = decode_token(token)

        if payload.get("type") != token_type:
            return None

        if "sub" not in payload:
            logger.debug("Token missing 'sub' claim")
            return None

        return payload

    except JWTError as e:
        logger.debug(f"Token validation failed: {e}")
        return None