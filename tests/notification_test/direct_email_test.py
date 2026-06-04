import aiosmtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def test_email():
    async with aiosmtplib.SMTP(
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True
    ) as smtp:
        await smtp.login("YaqidhTeam@gmail.com", "YOUR_GMAIL_APP_PASSWORD")
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Test"
        msg["From"] = "YaqidhTeam@gmail.com"
        msg["To"] = "RECEIVER_EMAIL@gmail.com"
        msg.attach(MIMEText("Test", "html"))
        
        await smtp.sendmail("YaqidhTeam@gmail.com", "RECEIVER_EMAIL@gmail.com", msg.as_string())
        print("✅ Email sent!")

asyncio.run(test_email())