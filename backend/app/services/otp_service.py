import random
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.otp_verification import OTPVerification
from app.services.email import send_otp_email

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10
MAX_FAILED_ATTEMPTS = 6


async def generate_and_send_otp(
    phone_number: str,
    db: AsyncSession
) -> dict:
    """
    Generate OTP and send via email to user's registered email address.
    
    Returns:
        {
            "success": bool,
            "message": str,
            "user_id": str (if success),
            "expires_in_minutes": int
        }
    """
    try:
        # Find user by phone number
        result = await db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"OTP request for non-existent phone: {phone_number}")
            return {
                "success": False,
                "message": "Phone number not found in our system"
            }
        
        # Check the most recent non-verified OTP attempt for rate limiting
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(OTPVerification)
            .where(OTPVerification.user_id == user.user_id)
            .where(OTPVerification.verified == False)
            .where(OTPVerification.expires_at > now)
            .order_by(OTPVerification.created_at.desc())
        )
        existing_otp = result.scalars().first()
        
        if existing_otp and existing_otp.failed_attempts >= MAX_FAILED_ATTEMPTS:
            logger.warning(f"Max OTP attempts exceeded for user {user.user_id}")
            return {
                "success": False,
                "message": f"Too many failed attempts. Please try again in {OTP_EXPIRY_MINUTES} minutes"
            }
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Create OTP record in database
        expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
        
        otp_record = OTPVerification(
            user_id=user.user_id,
            otp_code=otp_code,
            created_at=now,
            expires_at=expires_at,
            verified=False,
            failed_attempts=0
        )
        
        db.add(otp_record)
        await db.commit()
        
        # Send OTP via email
        email_sent = await send_otp_email(
            user_email=user.email,
            user_name=user.full_name or "User",
            otp_code=otp_code,
            expiry_minutes=OTP_EXPIRY_MINUTES
        )
        
        if not email_sent:
            logger.error(f"Failed to send OTP email to {user.email}")
            return {
                "success": False,
                "message": "Failed to send OTP. Please try again"
            }
        
        logger.info(f"OTP sent successfully to {user.email} for phone {phone_number}")
        
        return {
            "success": True,
            "message": f"OTP sent to your registered email address",
            "user_id": str(user.user_id),
            "expires_in_minutes": OTP_EXPIRY_MINUTES
        }
    
    except Exception as e:
        logger.error(f"Error in generate_and_send_otp: {str(e)}")
        return {
            "success": False,
            "message": "An error occurred. Please try again"
        }


async def verify_otp(
    phone_number: str,
    otp_code: str,
    db: AsyncSession
) -> dict:
    """
    Verify OTP code for user.
    
    Returns:
        {
            "success": bool,
            "message": str,
            "user_id": str (if success),
            "access_token": str (if success)
        }
    """
    try:
        # Find user by phone number
        result = await db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {
                "success": False,
                "message": "Phone number not found"
            }
        
        # Find valid (non-expired, non-verified) OTP record
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(OTPVerification)
            .where(OTPVerification.user_id == user.user_id)
            .where(OTPVerification.verified == False)
            .where(OTPVerification.expires_at > now)
            .order_by(OTPVerification.created_at.desc())
        )
        otp_record = result.scalars().first()
        
        if not otp_record:
            return {
                "success": False,
                "message": "No valid OTP found. Please request a new one"
            }
        
        # Check if max attempts exceeded
        if otp_record.failed_attempts >= MAX_FAILED_ATTEMPTS:
            return {
                "success": False,
                "message": f"Too many failed attempts. OTP expired. Request a new one"
            }
        
        # Verify OTP code
        if otp_record.otp_code != otp_code:
            otp_record.failed_attempts += 1
            await db.commit()
            
            remaining_attempts = MAX_FAILED_ATTEMPTS - otp_record.failed_attempts
            logger.warning(f"Invalid OTP attempt for user {user.user_id}. Remaining: {remaining_attempts}")
            
            if remaining_attempts <= 0:
                return {
                    "success": False,
                    "message": "Too many failed attempts. This OTP is now locked. Request a new one"
                }
            
            return {
                "success": False,
                "message": f"Invalid OTP. {remaining_attempts} attempts remaining"
            }
        
        # Mark OTP as verified
        otp_record.verified = True
        await db.commit()
        
        logger.info(f"OTP verified successfully for user {user.user_id}")
        
        # Generate JWT token (use existing JWT logic)
        from app.auth.jwt import create_access_token
        
        access_token = create_access_token(
            data={"sub": str(user.user_id), "role": user.role_name}
        )
        
        return {
            "success": True,
            "message": "OTP verified successfully",
            "user_id": str(user.user_id),
            "access_token": access_token
        }
    
    except Exception as e:
        logger.error(f"Error in verify_otp: {str(e)}")
        return {
            "success": False,
            "message": "An error occurred during verification"
        }
