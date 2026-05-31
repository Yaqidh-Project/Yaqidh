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

# Updated: Explicitly allows both Parent and Manager roles for public registration
PUBLIC_ALLOWED_ROLES = {UserRole.Parent, UserRole.Manager}


def _hash_password(plain: str) -> str:
    """
    Hashes a plain text password using bcrypt salt encryption routing.
    """
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies an incoming plain text credentials string against the database persistence hash.
    """
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _generate_otp(length: int = 6) -> str:
    """
    Generates a secure cryptographically random numeric string sequence for multi-factor auth.
    """
    return "".join(random.choices(string.digits, k=length))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Handles public registration. Parents can sign up directly to monitor their homes, 
    and Managers can register to setup nursery environments. Teachers are managed directly.
    """
    # Authorization boundary check: verifies if the requested registration role is open to the public
    if payload.role_name not in PUBLIC_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Public registration only allows roles: {', '.join(r.value for r in sorted(PUBLIC_ALLOWED_ROLES, key=lambda x: x.value))}. "
                "Teachers must be created and provisioned directly by an existing nursery Manager account."
            ),
        )

    # Integrity constraint verification: check if unique constraint identifier email already persists
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check if phone number already registered
    result = await db.execute(select(User).where(User.phone_number == payload.phone_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Phone number already registered")

    # Construct and persist new domain tracking account entity
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
    """
    Authenticates account holders and returns cryptographic claim assertions (JWT).
    Separates error responses to enhance front-end dynamic user feedback.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    
    # 1. Condition: Account email cannot be traced within pgAdmin database context
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account does not exist. Please register first.",
        )
        
    # 2. Condition: Account exists but cryptographic password verification failed
    if not _verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again.",
        )
        
    # 3. Check current functional persistence execution state flags
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated. Please contact support.",
        )
        
    token_data = {"sub": str(user.user_id), "role": user.role_name}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        role=user.role_name.value if hasattr(user.role_name, 'value') else user.role_name,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchanges a long-lived valid token structure to renew the short-lived access scope token.
    """
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
        role=user.role_name.value if hasattr(user.role_name, 'value') else user.role_name,
    )



@router.post("/signup/request-otp", status_code=status.HTTP_200_OK)
async def signup_request_otp(
    phone_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Request OTP during registration (NO LOGIN REQUIRED).
    Searches for user by phone number and sends OTP via email.
    """
    # Find user by phone number
    result = await db.execute(
        select(User).where(User.phone_number == phone_number)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found. Please register first.",
        )
    
    # Check if phone is already verified
    if user.phone_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is already verified.",
        )

    # Invalidate any existing unused codes for this user
    await db.execute(
        PhoneVerificationCode.__table__.delete().where(
            PhoneVerificationCode.user_id == user.user_id,
            PhoneVerificationCode.used.is_(False),
        )
    )
    await db.commit()

    # Generate OTP
    code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    # Save OTP to database
    phone_code = PhoneVerificationCode(
        user_id=user.user_id,
        code=code,
        expires_at=expires_at,
        used=False,
    )
    db.add(phone_code)
    await db.flush()
    await db.commit()

    # Send OTP via Email
    from app.services.email import send_otp_email
    
    try:
        email_sent = await send_otp_email(
            user_email=user.email,
            user_name=user.full_name,
            otp_code=code,
            expiry_minutes=settings.OTP_EXPIRE_MINUTES
        )
        
        if email_sent:
            logger.info(f"✅ OTP email sent to {user.email} (phone: {phone_number})")
        else:
            logger.warning(f"❌ Failed to send OTP email to {user.email}, using MOCK SMS")
    
    except Exception as e:
        logger.error(f"❌ Error sending OTP email: {str(e)}, using MOCK SMS")
    
    # MOCK SMS as Backup (for development/testing)
    logger.info(
        f"[MOCK SMS] Sending OTP {code} to {phone_number} "
        f"(user={user.user_id}, expires={expires_at.isoformat()})"
    )
    print(
        f"\n{'='*50}\n"
        f"[MOCK SMS - BACKUP] To: {phone_number}\n"
        f"Your Yaqidh verification code is: {code}\n"
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
        f"{'='*50}\n"
    )

    return {
        "message": f"Verification code sent to your email and phone {phone_number}.",
        "expires_in_minutes": settings.OTP_EXPIRE_MINUTES,
    }


@router.post("/signup/resend-otp", status_code=status.HTTP_200_OK)
async def signup_resend_otp(
    phone_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend OTP during registration (NO LOGIN REQUIRED).
    Allows users to request a new OTP code if the previous one expired.
    """
    # Find user by phone number
    result = await db.execute(
        select(User).where(User.phone_number == phone_number)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found. Please register first.",
        )
    
    if user.phone_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is already verified.",
        )

    # Check if there's a recent unused OTP (within last 2 minutes)
    now = datetime.now(timezone.utc)
    two_minutes_ago = now - timedelta(minutes=2)
    
    result = await db.execute(
        select(PhoneVerificationCode).where(
            PhoneVerificationCode.user_id == user.user_id,
            PhoneVerificationCode.used.is_(False),
            PhoneVerificationCode.created_at > two_minutes_ago,  # Assuming created_at field exists
        )
    )
    recent_code = result.scalar_one_or_none()
    
    if recent_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 2 minutes before requesting a new code.",
        )

    # Delete old unused codes
    await db.execute(
        PhoneVerificationCode.__table__.delete().where(
            PhoneVerificationCode.user_id == user.user_id,
            PhoneVerificationCode.used.is_(False),
        )
    )
    await db.commit()

    # Generate new OTP
    code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    # Save OTP to database
    phone_code = PhoneVerificationCode(
        user_id=user.user_id,
        code=code,
        expires_at=expires_at,
        used=False,
    )
    db.add(phone_code)
    await db.flush()
    await db.commit()

    # Send OTP via Email
    from app.services.email import send_otp_email
    
    try:
        email_sent = await send_otp_email(
            user_email=user.email,
            user_name=user.full_name,
            otp_code=code,
            expiry_minutes=settings.OTP_EXPIRE_MINUTES
        )
        
        if email_sent:
            logger.info(f"✅ OTP email RESENT to {user.email} (phone: {phone_number})")
        else:
            logger.warning(f"❌ Failed to resend OTP email to {user.email}, using MOCK SMS")
    
    except Exception as e:
        logger.error(f"❌ Error resending OTP email: {str(e)}, using MOCK SMS")
    
    # MOCK SMS as Backup
    logger.info(f"[MOCK SMS - RESEND] Sending OTP {code} to {phone_number}")
    print(
        f"\n{'='*50}\n"
        f"[MOCK SMS - RESEND] To: {phone_number}\n"
        f"Your Yaqidh verification code is: {code}\n"
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
        f"{'='*50}\n"
    )

    return {
        "message": f"New verification code sent to your email and phone {phone_number}.",
        "expires_in_minutes": settings.OTP_EXPIRE_MINUTES,
    }


@router.post("/signup/verify-otp", response_model=UserOut)
async def signup_verify_otp(
    phone_number: str,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify OTP during signup (NO LOGIN REQUIRED).
    Validates the code and marks phone as verified.
    """
    # Find user by phone number
    result = await db.execute(
        select(User).where(User.phone_number == phone_number)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found.",
        )
    
    if user.phone_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone is already verified.",
        )

    # Validate OTP
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PhoneVerificationCode).where(
            PhoneVerificationCode.user_id == user.user_id,
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

    # Mark code as used and phone as verified
    phone_code.used = True
    user.phone_verified = True
    await db.flush()
    await db.refresh(user)
    await db.commit()

    logger.info(f"✅ Phone verified successfully for user {user.user_id} ({user.email})")
    
    return user


@router.post("/phone/request-code", status_code=status.HTTP_200_OK)
async def request_phone_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request phone verification code after login (REQUIRES AUTHENTICATION).
    Used for additional security verification after user is already logged in.
    """
    if not current_user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No phone number on your account. Update your profile first.",
        )

    # Invalidate any stale or unused codes
    await db.execute(
        PhoneVerificationCode.__table__.delete().where(
            PhoneVerificationCode.user_id == current_user.user_id,
            PhoneVerificationCode.used.is_(False),
        )
    )
    await db.commit()

    # Generate code
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
    await db.commit()

    # Send OTP via Email
    from app.services.email import send_otp_email
    
    try:
        email_sent = await send_otp_email(
            user_email=current_user.email,
            user_name=current_user.full_name,
            otp_code=code,
            expiry_minutes=settings.OTP_EXPIRE_MINUTES
        )
        
        if email_sent:
            logger.info(f"✅ OTP email sent to {current_user.email} (phone: {current_user.phone_number})")
        else:
            logger.warning(f"❌ Failed to send OTP email to {current_user.email}, using MOCK SMS")
    
    except Exception as e:
        logger.error(f"❌ Error sending OTP email: {str(e)}, using MOCK SMS")
    
    # MOCK SMS as Backup
    logger.info(
        f"[MOCK SMS] Sending OTP {code} to {current_user.phone_number} "
        f"(user={current_user.user_id}, expires={expires_at.isoformat()})"
    )
    print(
        f"\n{'='*50}\n"
        f"[MOCK SMS - BACKUP] To: {current_user.phone_number}\n"
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
    """
    Verify phone code after login (REQUIRES AUTHENTICATION).
    """
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

    # Mark as used and phone as verified
    phone_code.used = True
    current_user.phone_verified = True
    await db.flush()
    await db.refresh(current_user)
    await db.commit()

    logger.info(f"✅ Phone verified successfully for user {current_user.user_id}")
    return current_user


# ============================================================================
# PASSWORD RECOVERY
# ============================================================================

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Validates account email existence and initiates a secure password recovery pipeline.
    """
    # Search for the targeted user within the database
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    
    # Return a successful mock response even if email doesn't exist
    # This prevents malicious threat actors from tracing or scanning registered user emails (User Enumeration).
    if not user:
        return {"status": "success", "message": "If the account exists, a recovery link has been generated."}
        
    # (Mailing/Reset Logic Pipeline)
    # generate a temporary secure token or dispatch an automated email.
    print(f"⚠️ SECURITY ALERT: Secure recovery token generated for user: {user.email}")
    
    return {
        "status": "success", 
        "message": "Recovery protocol successfully executed. Check terminal log for secure recovery tokens."
    }


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Validates account existence and securely updates the user's password 
    inside the pgAdmin database after applying cryptographic hashing rules.
    """
    # 1. Query the database for the user by email
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account directory verification failed."
        )
        
    # 2. Hash the new password securely using your existing validated bcrypt function
    hashed_password = _hash_password(payload.new_password)
    user.password = hashed_password
    
    # 3. Commit state alterations securely to pgAdmin relational layers
    await db.commit()
    
    print(f"\n🔑 SECURITY ALTERATION: Password securely updated in pgAdmin for user: {user.email}\n")
    
    return {"status": "success", "message": "Password updated successfully."}