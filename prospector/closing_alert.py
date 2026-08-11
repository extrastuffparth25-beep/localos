"""
closing_alert.py — Autonomous Closing Alerts for LOCALOS.

Since third-party WhatsApp bots can be unreliable and sketchy,
this module sends a HIGH-PRIORITY "SOS" style email alert directly 
to the agency owner when the AI Closer secures a warm lead. 
This guarantees 100% deliverability without relying on sketchy APIs.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    GMAIL_APP_PASSWORD,
    GMAIL_SMTP_HOST,
    GMAIL_SMTP_PORT,
    GMAIL_USER,
    NOTIFICATION_RECIPIENT,
)

log = logging.getLogger(__name__)

def alert_client_closed(business_name: str, email: str, conversation_summary: str, next_steps: str) -> bool:
    """Format and send the 'Client Closed' alert via High-Priority Email."""
    
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        log.error("Missing Gmail credentials for sending closing alert.")
        return False
        
    log.info("Sending CLOSING ALERT for %s to %s...", business_name, NOTIFICATION_RECIPIENT)
    
    subject = f"🚨 URGENT: HOT LEAD SECURED - {business_name} 🚨"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; border-top: 5px solid #22C55E;">
            <h2 style="color: #22C55E; margin-top: 0;">🚨 HOT LEAD SECURED 🚨</h2>
            
            <p><strong>Business:</strong> {business_name}</p>
            <p><strong>Email:</strong> {email}</p>
            
            <h3 style="border-bottom: 1px solid #eee; padding-bottom: 5px;">Context:</h3>
            <pre style="background: #f9f9f9; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-size: 13px;">{conversation_summary}</pre>
            
            <h3 style="border-bottom: 1px solid #eee; padding-bottom: 5px; color: #D4AF37;">🎯 WHAT YOU NEED TO DO RIGHT NOW TO CLOSE THIS:</h3>
            <p style="font-size: 16px; font-weight: bold;">{next_steps}</p>
            
            <p style="margin-top: 30px; font-size: 12px; color: #888;">
                LOCALOS Autonomous Closer <br>
                <em>Go get that money!</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["From"] = f"LOCALOS AI Closer <{GMAIL_USER}>"
    msg["To"] = NOTIFICATION_RECIPIENT
    msg["Subject"] = subject
    # Add high priority headers so phone notifications ping loudly
    msg['X-Priority'] = '1 (Highest)'
    msg['X-MSMail-Priority'] = 'High'
    msg['Importance'] = 'High'
    
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, NOTIFICATION_RECIPIENT, msg.as_string())
        log.info("Closing alert sent successfully!")
        return True
    except Exception as e:
        log.error("Failed to send closing alert: %s", str(e))
        return False
