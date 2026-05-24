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
    zone_name: str,
    timestamp: datetime,
    confidence: float,
    incident_clip_url: str = None,
    camera_name: str = None,
) -> bool:
    """
    Send incident notification email via Gmail SMTP.
    """
    settings = get_settings()
    
    test_email = os.getenv("MANAGER_TEST_EMAIL")
    if test_email:
        email_recipient = test_email
        logger.info(f"Using test email override: {test_email}")
    else:
        email_recipient = user_email
        logger.info(f"Using production email: {user_email}")
    
    subject = f"🚨 {incident_type.capitalize()} Detected in {zone_name}"
    
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    confidence_pct = confidence * 100
    
    video_link = f'<p><a href="{incident_clip_url}">View Video</a></p>' if incident_clip_url else ""
    
    body = f"""<!DOCTYPE html>
<html>
<body>
<h2>Incident Alert</h2>
<p><strong>Type:</strong> {incident_type}</p>
<p><strong>Zone:</strong> {zone_name}</p>
<p><strong>Camera:</strong> {camera_name or 'Unknown'}</p>
<p><strong>Time:</strong> {timestamp_str}</p>
<p><strong>Confidence:</strong> {confidence_pct:.1f}%</p>
{video_link}
<p>Please check the dashboard for more details.</p>
</body>
</html>"""
    
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