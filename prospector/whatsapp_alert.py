"""
whatsapp_alert.py — Autonomous Closing Alerts via WhatsApp.

Sends an instant WhatsApp message to the agency owner when the AI Closer
secures a warm lead or closes a deal. Uses the free CallMeBot API.
"""

import logging
import urllib.parse
import urllib.request
import os

log = logging.getLogger(__name__)

# User's phone number provided in the prompt
OWNER_PHONE = "6364143827" 
# Needs to have country code attached, assuming +91 for Indian number
OWNER_PHONE_FULL = f"+91{OWNER_PHONE}"

# To use this free API, the user needs to get an API key by messaging the bot:
# 1. Add +34 624 543 328 to Contacts
# 2. Send "I allow callmebot to send me messages" via WhatsApp
# 3. The bot replies with an API key.
CALLMEBOT_API_KEY = os.environ.get("CALLMEBOT_API_KEY", "")

def send_whatsapp_alert(message: str) -> bool:
    """Send a WhatsApp message using the free CallMeBot API."""
    if not CALLMEBOT_API_KEY:
        log.warning("WhatsApp API key not set. Cannot send alert to %s", OWNER_PHONE_FULL)
        return False
        
    log.info("Sending WhatsApp alert to %s...", OWNER_PHONE_FULL)
    
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={OWNER_PHONE_FULL.replace('+', '')}&text={encoded_message}&apikey={CALLMEBOT_API_KEY}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                log.info("WhatsApp alert sent successfully!")
                return True
            else:
                log.error("Failed to send WhatsApp alert. Status: %s", response.status)
                return False
    except Exception as e:
        log.error("Error sending WhatsApp alert: %s", str(e))
        return False

def alert_client_closed(business_name: str, email: str, conversation_summary: str, next_steps: str) -> None:
    """Format and send the specific 'Client Closed' alert."""
    msg = f"""🚨 *HOT LEAD SECURED* 🚨

🏢 *Business:* {business_name}
✉️ *Email:* {email}

💬 *Context:*
{conversation_summary}

🎯 *WHAT YOU NEED TO DO RIGHT NOW TO CLOSE THIS:*
{next_steps}

💰 Get that money!"""
    send_whatsapp_alert(msg)
