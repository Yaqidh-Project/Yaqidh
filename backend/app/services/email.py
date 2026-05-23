import aiosmtplib
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
    
    Args:
        user_email: Recipient email address
        incident_type: "fall" or "violence"
        zone_name: Name of the zone where incident occurred
        timestamp: When the incident was detected
        confidence: Model confidence score (0.0-1.0)
        incident_clip_url: URL to video clip (optional)
        camera_name: Name of the camera (optional)
    
    Returns:
        True if email sent successfully
        False if email sending failed (will not raise exception)
    """
    settings = get_settings()
    
    # Build email subject
    subject = f"🚨 {incident_type.capitalize()} Detected in {zone_name}"
    
    # Format timestamp and confidence for display
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    confidence_pct = confidence * 100
    
    # Build HTML body with optional video link
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
        async with aiosmtplib.SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT) as smtp:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SENDER_EMAIL
            msg["To"] = user_email
            
            msg.attach(MIMEText(body, "html"))
            
            await smtp.sendmail(settings.SENDER_EMAIL, user_email, msg.as_string())
        
        logger.info(f"Email sent to {user_email} for {incident_type} incident")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {str(e)}")
        return False
