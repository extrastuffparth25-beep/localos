"""
bounce_detector.py — Safeguards the Gmail sender reputation.

Scans the inbox for bounce/failure delivery notifications. If found,
it extracts the dead email address and updates its status to 'Bounced'
so the Drip Engine never emails it again.
"""

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

def extract_bounced_email(subject: str, body: str) -> str | None:
    """
    Looks for signs of an email bounce and tries to extract the failed address.
    Returns the bounced email address, or None if not a bounce.
    """
    bounce_indicators = [
        "delivery status notification",
        "undeliverable",
        "message not delivered",
        "delivery failure",
        "returned to sender"
    ]
    
    subject_lower = subject.lower()
    is_bounce = any(indicator in subject_lower for indicator in bounce_indicators)
    
    if not is_bounce:
        return None
        
    # Try to extract the failed email address from the body
    # Gmail usually says: "Your message to xxx@yyy.com couldn't be delivered."
    match = re.search(r"Your message to ([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}) couldn't be delivered", body)
    if match:
        return match.group(1).lower()
        
    # Fallback generic extraction
    match = re.search(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", body)
    if match:
        return match.group(1).lower()
        
    return None
