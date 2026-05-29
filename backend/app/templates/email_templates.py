def get_incident_email_html(
    user_role: str,
    incident_type: str,
    camera_id: str,
    camera_name: str,
    zone_id: str,
    zone_name: str,
    timestamp_str: str,
    confidence_pct: float,
    incident_clip_url: str = None
) -> str:
    video_section = (
        f'📹 <a href="{incident_clip_url}" style="color: #d32f2f; font-weight: bold; text-decoration: underline;">View Video Clip</a>'
        if incident_clip_url
        else "Video clip will be available shortly in the dashboard."
    )
    
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 650px; margin: 20px auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); background: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); color: white; padding: 30px 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 26px; font-weight: bold; letter-spacing: 0.5px; }}
        .divider {{ background: #b71c1c; height: 4px; }}
        .content {{ padding: 30px; background: #ffffff; }}
        .greeting {{ font-size: 16px; margin-bottom: 15px; color: #222; }}
        .greeting strong {{ color: #d32f2f; }}
        .message {{ font-size: 14px; margin-bottom: 25px; line-height: 1.8; color: #555; }}
        .details-box {{ background: #fdfdfd; border-left: 4px solid #d32f2f; border-top: 1px solid #f0f0f0; border-right: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0; padding: 20px; border-radius: 0 4px 4px 0; margin: 20px 0; }}
        .detail-row {{ margin: 12px 0; font-size: 14px; border-bottom: 1px dotted #eeeeee; padding-bottom: 8px; }}
        .detail-row:last-child {{ border-bottom: none; padding-bottom: 0; }}
        .detail-label {{ font-weight: bold; display: inline-block; width: 150px; color: #333; vertical-align: top; }}
        .detail-value {{ display: inline-block; color: #555; vertical-align: top; }}
        .video-section {{ text-align: center; padding: 18px; background: #f9f9f9; border: 1px dashed #d32f2f; border-radius: 6px; margin: 25px 0; font-size: 14px; color: #444; }}
        .action-required {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 0 4px 4px 0; margin: 20px 0; font-weight: bold; color: #856404; font-size: 13px; line-height: 1.5; }}
        .footer {{ background: #f9f9f9; padding: 25px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee; }}
        .footer p {{ margin: 6px 0; }}
        .footer-heart {{ color: #d32f2f; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Attention Required</h1>
        </div>
        <div class="divider"></div>
        
        <div class="content">
            <div class="greeting">
                Dear <strong>{user_role.capitalize()}</strong>,
            </div>
            
            <div class="message">
                A real-time safety alert has been triggered in the monitored daycare environment.
                Please review the details of the detected incident below:
            </div>
            
            <div class="details-box">
                <div class="detail-row">
                    <span class="detail-label">🎯 Event Type:</span>
                    <span class="detail-value" style="font-weight: 600; color: #d32f2f;">{incident_type.capitalize()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📹 Camera:</span>
                    <span class="detail-value">{camera_name} <span style="color:#999; font-size:12px;">(ID: {camera_id})</span></span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📍 Zone:</span>
                    <span class="detail-value">{zone_name} <span style="color:#999; font-size:12px;">(ID: {zone_id})</span></span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">⏰ Timestamp:</span>
                    <span class="detail-value">{timestamp_str}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📊 Confidence:</span>
                    <span class="detail-value" style="font-weight: 600;">{confidence_pct:.1f}%</span>
                </div>
            </div>
            
            <div class="video-section">
                {video_section}
            </div>
            
            <div class="action-required">
                ⚠️ ACTION REQUIRED: Please log in to your Yaqidh Incident Log immediately to review the incident.
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Yaqidh Intelligent Monitoring System</strong></p>
            <p>© 2026 Yaqidh. All rights reserved.</p>
            <p>Made with <span class="footer-heart">❤️</span> by Yaqidh Academic Team</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_body


def get_otp_email_html(
    user_name: str,
    otp_code: str,
    expiry_minutes: int
) -> str:
    """
    Generate HTML email template for OTP verification code.
    """
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 500px; margin: 20px auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); background: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%); color: white; padding: 30px 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 26px; font-weight: bold; letter-spacing: 0.5px; }}
        .divider {{ background: #388E3C; height: 4px; }}
        .content {{ padding: 30px; background: #ffffff; }}
        .greeting {{ font-size: 16px; margin-bottom: 20px; color: #222; }}
        .greeting strong {{ color: #4CAF50; }}
        .message {{ font-size: 14px; margin-bottom: 30px; line-height: 1.8; color: #555; }}
        .otp-box {{ background: #f0f7f0; border: 2px solid #4CAF50; border-radius: 8px; padding: 25px; text-align: center; margin: 30px 0; }}
        .otp-label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }}
        .otp-code {{ font-size: 36px; font-weight: bold; color: #4CAF50; letter-spacing: 4px; font-family: 'Courier New', monospace; margin: 15px 0; }}
        .otp-expiry {{ font-size: 13px; color: #888; margin-top: 10px; }}
        .info-box {{ background: #fffbea; border-left: 4px solid #FFC107; padding: 15px; border-radius: 0 4px 4px 0; margin: 20px 0; font-size: 13px; color: #8B6F47; line-height: 1.6; }}
        .footer {{ background: #f9f9f9; padding: 25px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee; }}
        .footer p {{ margin: 6px 0; }}
        .footer-heart {{ color: #4CAF50; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Verify Your Account</h1>
        </div>
        <div class="divider"></div>
        
        <div class="content">
            <div class="greeting">
                Hi <strong>{user_name}</strong>,
            </div>
            
            <div class="message">
                Your account verification has been initiated. Use the code below to complete your login.
            </div>
            
            <div class="otp-box">
                <div class="otp-label">Your Verification Code</div>
                <div class="otp-code">{otp_code}</div>
                <div class="otp-expiry">Expires in {expiry_minutes} minutes</div>
            </div>
            
            <div class="info-box">
                <strong>🔒 Security Notice:</strong> Never share this code with anyone. Yaqidh staff will never ask for your verification code.
            </div>
            
            <div class="message" style="margin-top: 25px; color: #666; font-size: 13px;">
                If you did not request this code, please ignore this email or contact our support team.
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Yaqidh Intelligent Monitoring System</strong></p>
            <p>© 2026 Yaqidh. All rights reserved.</p>
            <p>Made with <span class="footer-heart">❤️</span> by Yaqidh Academic Team</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_body