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

def get_email_body(msg) -> str:
    """Extract plain text body from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    return part.get_payload(decode=True).decode()
                except:
                    pass
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            try:
                return msg.get_payload(decode=True).decode()
            except:
                pass
    return ""

def scan_for_replies(prospect_emails: list[str]) -> list[dict[str, str]]:
    """
    Connect to Gmail via IMAP, find unread emails from prospect emails,
    extract the message, mark as read, and return the data.
    """
    if not OUTREACH_GMAIL_USER or not OUTREACH_GMAIL_APP_PASSWORD:
        log.warning("Outreach Gmail credentials not set. Skipping inbox scan.")
        return []

    log.info("Scanning inbox for replies from prospects...")
    replies = []

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
                    
                    if sender_email in [e.lower() for e in prospect_emails]:
                        log.info("Found reply from prospect: %s", sender_email)
                        
                        # Get Subject
                        subject, encoding = decode_header(msg.get("Subject", ""))[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                            
                        body = clean_text(get_email_body(msg))
                        
                        replies.append({
                            "email": sender_email,
                            "subject": subject,
                            "body": body
                        })
                        
                        # Mark as read (it's already read by fetching, but this ensures it)
                        mail.store(e_id, '+FLAGS', '\Seen')

        mail.logout()
        
    except Exception as e:
        log.error("IMAP Error during inbox scan: %s", str(e))
        
    return replies
