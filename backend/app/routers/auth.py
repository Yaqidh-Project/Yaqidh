import uuid
import logging
import random
import string
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt

from app.database import get_db
from app.models.user import User
from app.models.phone_code import PhoneVerificationCode
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserCreate, UserOut
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.models.enums import UserRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

PUBLIC_ALLOWED_ROLES = {UserRole.Parent}


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    if payload.role_name not in PUBLIC_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Public registration only allows roles: {', '.join(r.value for r in sorted(PUBLIC_ALLOWED_ROLES, key=lambda x: x.value))}. "
                "Teachers are created by a Manager. "
                "Manager accounts require an invitation from an existing Manager."
            ),
        )

    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password=_hash_password(payload.password),
        phone_number=payload.phone_number,
        role_name=payload.role_name,
        notification_prefs=payload.notification_prefs,
        phone_verified=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    await db.commit()
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not _verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated. Please contact support.",
        )
    token_data = {"sub": str(user.user_id), "role": user.role_name}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_payload = verify_token(payload.refresh_token, token_type="refresh")
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    try:
        user_id = uuid.UUID(token_payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: invalid user identifier",
        )
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated. Please contact support.",
        )
    token_data = {"sub": str(user.user_id), "role": user.role_name}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/phone/request-code", status_code=status.HTTP_200_OK)
async def request_phone_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No phone number on your account. Update your profile first.",
        )

    await db.execute(
        PhoneVerificationCode.__table__.delete().where(
            PhoneVerificationCode.user_id == current_user.user_id,
            PhoneVerificationCode.used.is_(False),
        )
    )

    code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    phone_code = PhoneVerificationCode(
        user_id=current_user.user_id,
        code=code,
        expires_at=expires_at,
        used=False,
    )
    db.add(phone_code)
    await db.flush()

    logger.info(
        f"[MOCK SMS] Sending OTP {code} to {current_user.phone_number} "
        f"(user={current_user.user_id}, expires={expires_at.isoformat()})"
    )
    print(
        f"\n{'='*50}\n"
        f"[MOCK SMS] To: {current_user.phone_number}\n"
        f"Your Yaqidh verification code is: {code}\n"
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
        f"{'='*50}\n"
    )

    return {
        "message": f"Verification code sent to {current_user.phone_number}.",
        "expires_in_minutes": settings.OTP_EXPIRE_MINUTES,
    }


@router.post("/phone/verify-code", response_model=UserOut)
async def verify_phone_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PhoneVerificationCode).where(
            PhoneVerificationCode.user_id == current_user.user_id,
            PhoneVerificationCode.code == code,
            PhoneVerificationCode.used.is_(False),
            PhoneVerificationCode.expires_at > now,
        )
    )
    phone_code = result.scalar_one_or_none()
    if not phone_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    phone_code.used = True
    current_user.phone_verified = True
    await db.flush()
    await db.refresh(current_user)

    logger.info(f"Phone verified for user {current_user.user_id}")
    return current_user
