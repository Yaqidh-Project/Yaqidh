import aiosmtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


async def send_incident_email(
    user_email: str,
    incident_type: str,
    zone_id: str,
    zone_name: str,
    camera_id: str,
    camera_name: str,
    timestamp: datetime,
    confidence: float,
    user_role: str,
    incident_clip_url: str = None,
) -> bool:
    settings = get_settings()
    
    test_email = os.getenv("MANAGER_TEST_EMAIL")
    if test_email:
        email_recipient = test_email
        logger.info(f"Using test email override: {test_email}")
    else:
        email_recipient = user_email
        logger.info(f"Using production email: {user_email}")
    
    subject = f"🚨 Yaqidh Safety Alert"
    
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S AST")
    confidence_pct = confidence * 100
    
    from app.templates.email_templates import get_incident_email_html
    
    html_body = get_incident_email_html(
        user_role=user_role,
        incident_type=incident_type,
        camera_id=camera_id,
        camera_name=camera_name,
        zone_id=zone_id,
        zone_name=zone_name,
        timestamp_str=timestamp_str,
        confidence_pct=confidence_pct,
        incident_clip_url=incident_clip_url
    )
    
    body = html_body
    
    try:
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST, 
            port=settings.SMTP_PORT, 
            start_tls=True
        ) as smtp:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SENDER_EMAIL
            msg["To"] = email_recipient
            
            msg.attach(MIMEText(body, "html"))
            
            await smtp.sendmail(settings.SENDER_EMAIL, email_recipient, msg.as_string())
        
        logger.info(f"Email sent to {email_recipient} for {incident_type} incident")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {email_recipient}: {str(e)}")
        return False