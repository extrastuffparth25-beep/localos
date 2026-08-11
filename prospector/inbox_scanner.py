"""
inbox_scanner.py — Two-Way IMAP Scanner for LOCALOS.

Connects to the outreach Gmail account, scans for unread replies from
any email address listed in prospects.csv, marks them as read, and
passes the conversation to the AI Closer.
"""

import imaplib
import email
from email.header import decode_header
import logging
import re
import base64
from typing import Any

from config import OUTREACH_GMAIL_USER, OUTREACH_GMAIL_APP_PASSWORD

log = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Basic cleanup of email body text to remove excessive newlines and whitespace."""
    if not text:
        return ""
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def get_email_body_and_images(msg) -> tuple[str, list[dict[str, str]]]:
    """Extract plain text body and base64 encoded images from an email."""
    body_text = ""
    images = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body_text += part.get_payload(decode=True).decode()
                except:
                    pass
            elif content_type in ["image/jpeg", "image/png"] and part.get_payload(decode=True):
                try:
                    img_data = part.get_payload(decode=True)
                    b64_data = base64.b64encode(img_data).decode("utf-8")
                    images.append({
                        "mime_type": content_type,
                        "data": b64_data
                    })
                    log.info("Extracted %s attachment.", content_type)
                except Exception as e:
                    log.warning("Failed to extract image: %s", str(e))
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            try:
                body_text = msg.get_payload(decode=True).decode()
            except:
                pass
                
    return clean_text(body_text), images

def is_auto_responder(subject: str, body: str) -> bool:
    """Check if the email is an automated out-of-office reply."""
    indicators = [
        "out of office", "automatic reply", "auto-reply", "vacation",
        "autoreply", "thank you for your message", "away from my desk"
    ]
    text = (subject + " " + body).lower()
    return any(indicator in text for indicator in indicators)

def scan_for_replies(prospect_emails: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Connect to Gmail via IMAP, find unread emails.
    Returns (valid_replies, bounces).
    """
    if not OUTREACH_GMAIL_USER or not OUTREACH_GMAIL_APP_PASSWORD:
        log.warning("Outreach Gmail credentials not set. Skipping inbox scan.")
        return []

    log.info("Scanning inbox for replies and bounces...")
    replies = []
    bounces = []

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(OUTREACH_GMAIL_USER, OUTREACH_GMAIL_APP_PASSWORD)
        mail.select("inbox")

        # Search for all UNREAD emails
        status, messages = mail.search(None, "UNREAD")
        if status != "OK" or not messages[0]:
            log.info("No unread emails found.")
            mail.logout()
            return []

        email_ids = messages[0].split()
        
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extract Sender
                    sender = msg.get("From", "")
                    # Extract email address between < >
                    match = re.search(r'<(.+?)>', sender)
                    sender_email = match.group(1) if match else sender.strip()
                    sender_email = sender_email.lower()
                    
                    subject, encoding = decode_header(msg.get("Subject", ""))[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                        
                    body, images = get_email_body_and_images(msg)
                    
                    # Mark as read immediately
                    mail.store(e_id, '+FLAGS', '\\Seen')
                    
                    # Catch Bounces (Mailer-Daemon)
                    if "mailer-daemon" in sender_email or "postmaster" in sender_email:
                        bounces.append({"subject": subject, "body": body})
                        continue
                        
                    # Ignore auto-responders
                    if is_auto_responder(subject, body):
                        log.info("Ignored auto-responder from %s", sender_email)
                        continue
                        
                    if sender_email in [e.lower() for e in prospect_emails]:
                        log.info("Found valid reply from prospect: %s", sender_email)
                        replies.append({
                            "email": sender_email,
                            "subject": subject,
                            "body": body,
                            "images": images
                        })

        mail.logout()
        
    except Exception as e:
        log.error("IMAP Error during inbox scan: %s", str(e))
        
    return replies, bounces
