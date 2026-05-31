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
from app.schemas.auth import ForgotPasswordRequest
from fastapi import BackgroundTasks
from app.schemas.auth import ResetPasswordRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

PUBLIC_ALLOWED_ROLES = {UserRole.Parent, UserRole.Manager}

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

def display_otp_terminal(phone_number: str, otp_code: str, expiry_minutes: int):
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    🔐 OTP VERIFICATION CODE                   ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  📱 Phone: {phone_number:<50} ║
║  🔑 Code: {otp_code:<52} ║
║  ⏱️  Expires: {expiry_minutes} minutes                        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    if payload.role_name not in PUBLIC_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Public registration only allows roles: {', '.join(r.value for r in sorted(PUBLIC_ALLOWED_ROLES, key=lambda x: x.value))}. "
                "Teachers must be created and provisioned directly by an existing nursery Manager account."
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
    
    from app.services.email import send_otp_email
    
    code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    phone_code = PhoneVerificationCode(
        user_id=user.user_id,
        code=code,
        expires_at=expires_at,
        used=False,
    )
    db.add(phone_code)
    await db.flush()
    await db.commit()
    
    email_sent = await send_otp_email(
        user_email=user.email,
        user_name=user.full_name,
        otp_code=code,
        expiry_minutes=settings.OTP_EXPIRE_MINUTES
    )
    
    display_otp_terminal(
        phone_number=user.phone_number or "N/A",
        otp_code=code,
        expiry_minutes=settings.OTP_EXPIRE_MINUTES
    )
    
    if email_sent:
        logger.info(f"[REGISTER] ✅ OTP email sent to {user.email} | Code: {code}")
    else:
        logger.warning(f"[REGISTER] ⚠️ OTP email failed for {user.email} | Terminal backup used")
    
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "phone_verified": False,
        "message": "Account created. Verification code sent to email.",
        "next_step": "verify_phone",
        "verification_endpoint": "/auth/signup/verify-otp",
        "expires_in_minutes": settings.OTP_EXPIRE_MINUTES
    }

@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account does not exist. Please register first.",
        )
        
    if not _verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again.",
        )
    
    if not user.phone_verified:
        from app.services.email import send_otp_email
        
        await db.execute(
            PhoneVerificationCode.__table__.delete().where(
                PhoneVerificationCode.user_id == user.user_id,
                PhoneVerificationCode.used.is_(False),
            )
        )
        await db.commit()
        
        code = _generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        
        phone_code = PhoneVerificationCode(
            user_id=user.user_id,
            code=code,
            expires_at=expires_at,
            used=False,
        )
        db.add(phone_code)
        await db.flush()
        await db.commit()
        
        email_sent = await send_otp_email(
            user_email=user.email,
            user_name=user.full_name,
            otp_code=code,
            expiry_minutes=settings.OTP_EXPIRE_MINUTES
        )
        
        display_otp_terminal(
            phone_number=user.phone_number or "N/A",
            otp_code=code,
            expiry_minutes=settings.OTP_EXPIRE_MINUTES
        )
        
        if email_sent:
            logger.info(f"[LOGIN] ✅ OTP email sent to {user.email} | Code: {code} | Phone: {user.phone_number}")
        else:
            logger.warning(f"[LOGIN] ⚠️ OTP email failed for {user.email} | Terminal backup used")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "requires_verification": True,
                "message": "OTP sent to your email. Please verify your phone number.",
                "verification_endpoint": "/auth/signup/verify-otp",
                "expires_in_minutes": settings.OTP_EXPIRE_MINUTES
            }
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
        token_type="bearer",
        role=user.role_name.value if hasattr(user.role_name, 'value') else user.role_name,
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
        token_type="bearer",
        role=user.role_name.value if hasattr(user.role_name, 'value') else user.role_name,
    )

@router.post("/signup/request-otp", status_code=status.HTTP_200_OK)
async def signup_request_otp(phone_number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found. Please register first.")
    
    if user.phone_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is already verified.")

    await db.execute(PhoneVerificationCode.__table__.delete().where(PhoneVerificationCode.user_id == user.user_id, PhoneVerificationCode.used.is_(False)))
    await db.commit()

    code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    db.add(PhoneVerificationCode(user_id=user.user_id, code=code, expires_at=expires_at, used=False))
    await db.commit()

    from app.services.email import send_otp_email
    await send_otp_email(user.email, user.full_name, code, settings.OTP_EXPIRE_MINUTES)
    
    display_otp_terminal(phone_number, code, settings.OTP_EXPIRE_MINUTES)
    
    return {"message": "Verification code sent.", "expires_in_minutes": settings.OTP_EXPIRE_MINUTES}

@router.post("/signup/resend-otp", status_code=status.HTTP_200_OK)
async def signup_resend_otp(phone_number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found.")
    
    if user.phone_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is already verified.")

    await db.execute(PhoneVerificationCode.__table__.delete().where(PhoneVerificationCode.user_id == user.user_id, PhoneVerificationCode.used.is_(False)))
    await db.commit()

    code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    db.add(PhoneVerificationCode(user_id=user.user_id, code=code, expires_at=expires_at, used=False))
    await db.commit()

    from app.services.email import send_otp_email
    await send_otp_email(user.email, user.full_name, code, settings.OTP_EXPIRE_MINUTES)
    
    display_otp_terminal(phone_number, code, settings.OTP_EXPIRE_MINUTES)
    
    return {"message": "Verification code resent.", "expires_in_minutes": settings.OTP_EXPIRE_MINUTES}

@router.post("/signup/verify-otp", response_model=UserOut)
async def signup_verify_otp(phone_number: str, code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found.")
    
    result = await db.execute(
        select(PhoneVerificationCode).where(
            PhoneVerificationCode.user_id == user.user_id,
            PhoneVerificationCode.code == code,
            PhoneVerificationCode.used.is_(False),
            PhoneVerificationCode.expires_at > datetime.now(timezone.utc),
        )
    )
    phone_code = result.scalar_one_or_none()
    
    if not phone_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code.")

    phone_code.used = True
    user.phone_verified = True
    await db.commit()
    await db.refresh(user)

    return user

@router.post("/phone/request-code", status_code=status.HTTP_200_OK)
async def request_phone_code(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.phone_number:
        raise HTTPException(status_code=422, detail="No phone number on your account.")
    
    await db.execute(PhoneVerificationCode.__table__.delete().where(PhoneVerificationCode.user_id == current_user.user_id, PhoneVerificationCode.used.is_(False)))
    await db.commit()

    code = _generate_otp()
    db.add(PhoneVerificationCode(user_id=current_user.user_id, code=code, expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES), used=False))
    await db.commit()

    from app.services.email import send_otp_email
    await send_otp_email(current_user.email, current_user.full_name, code, settings.OTP_EXPIRE_MINUTES)
    
    return {"message": "Code sent.", "expires_in_minutes": settings.OTP_EXPIRE_MINUTES}

@router.post("/phone/verify-code", response_model=UserOut)
async def verify_phone_code(code: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PhoneVerificationCode).where(PhoneVerificationCode.user_id == current_user.user_id, PhoneVerificationCode.code == code, PhoneVerificationCode.used.is_(False), PhoneVerificationCode.expires_at > datetime.now(timezone.utc)))
    phone_code = result.scalar_one_or_none()
    
    if not phone_code:
        raise HTTPException(status_code=400, detail="Invalid or expired code.")

    phone_code.used = True
    current_user.phone_verified = True
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        return {"status": "success", "message": "If the account exists, a recovery link has been generated."}
    return {"status": "success", "message": "Recovery protocol executed."}

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found.")
    user.password = _hash_password(payload.new_password)
    await db.commit()
    return {"status": "success", "message": "Password updated successfully."}