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
    """
    Generate HTML email template for incident notification.
    """
    video_section = (
        f'📹 <a href="{incident_clip_url}">View Video Clip</a>'
        if incident_clip_url
        else "Video clip will be available shortly in the dashboard."
    )
    
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 650px; margin: 0 auto; border: 2px solid #d32f2f; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%); color: white; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: bold; }}
        .divider {{ background: #d32f2f; height: 3px; }}
        .content {{ padding: 30px; background: #fafafa; }}
        .greeting {{ font-size: 16px; margin-bottom: 15px; }}
        .greeting strong {{ color: #d32f2f; }}
        .message {{ font-size: 14px; margin-bottom: 25px; line-height: 1.8; }}
        .details-box {{ background: white; border-left: 4px solid #d32f2f; padding: 20px; border-radius: 4px; margin: 20px 0; }}
        .detail-row {{ display: flex; margin: 12px 0; font-size: 14px; }}
        .detail-label {{ font-weight: bold; min-width: 140px; color: #333; }}
        .detail-value {{ color: #666; }}
        .video-section {{ text-align: center; padding: 15px; background: #f0f0f0; border-radius: 4px; margin: 20px 0; font-size: 14px; }}
        .action-required {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 4px; margin: 20px 0; font-weight: bold; color: #856404; }}
        .footer {{ background: #f9f9f9; padding: 20px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
        .footer p {{ margin: 5px 0; }}
        .footer-heart {{ color: #d32f2f; }}
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
                Dear <strong>{user_role}</strong>,
            </div>
            
            <div class="message">
                A real-time safety alert has been triggered in the monitored zone.
                Please review the details of the detected incident below:
            </div>
            
            <div class="details-box">
                <div class="detail-row">
                    <span class="detail-label">🎯 Event Type:</span>
                    <span class="detail-value">{incident_type.capitalize()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📹 Camera:</span>
                    <span class="detail-value">{camera_name} ({camera_id})</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📍 Zone:</span>
                    <span class="detail-value">{zone_name} ({zone_id})</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">⏰ Timestamp:</span>
                    <span class="detail-value">{timestamp_str}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📊 Confidence:</span>
                    <span class="detail-value">{confidence_pct:.1f}%</span>
                </div>
            </div>
            
            <div class="video-section">
                {video_section}
            </div>
            
            <div class="action-required">
                ⚠️ ACTION REQUIRED: Please log in to your Yaqidh Incident Log immediately to review the incident.
            </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Yaqidh Intelligent Monitoring System</strong></p>
            <p>© 2026 Yaqidh. All rights reserved.</p>
            <p>Made with <span class="footer-heart">❤️</span> by Yaqidh Team</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_body
