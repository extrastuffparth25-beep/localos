"""
drafter.py — Auto-draft outreach emails in Gmail via IMAP for LOCALOS.

Creates Gmail drafts for each qualified prospect so you can review
and send them with one click.
"""

from __future__ import annotations

import email as email_lib
import imaplib
import logging
import smtplib
import time
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from config import (
    GMAIL_APP_PASSWORD,
    GMAIL_SMTP_HOST,
    GMAIL_SMTP_PORT,
    GMAIL_USER,
    NOTIFICATION_RECIPIENT,
    OUTREACH_GMAIL_APP_PASSWORD,
    OUTREACH_GMAIL_USER,
    OUTREACH_IMAP_HOST,
    OUTREACH_IMAP_PORT,
)
from outreach.email_agent import generate_outreach_sequence

log = logging.getLogger(__name__)


def _create_gmail_draft(
    to_email: str,
    subject: str,
    body_text: str,
) -> bool:
    """Create a draft in the outreach Gmail account via IMAP."""
    if not OUTREACH_GMAIL_USER or not OUTREACH_GMAIL_APP_PASSWORD:
        log.error("OUTREACH_GMAIL_USER or OUTREACH_GMAIL_APP_PASSWORD not set.")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = OUTREACH_GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    try:
        imap = imaplib.IMAP4_SSL(OUTREACH_IMAP_HOST, OUTREACH_IMAP_PORT)
        imap.login(OUTREACH_GMAIL_USER, OUTREACH_GMAIL_APP_PASSWORD)
        result = imap.append("[Gmail]/Drafts", "", None, msg.as_bytes())
        imap.logout()

        if result[0] == "OK":
            return True
        else:
            log.error("IMAP append failed: %s", result)
            return False
    except Exception as exc:
        log.error("Error creating draft for %s: %s", to_email, exc)
        return False


def draft_outreach_emails(
    leads: list[dict[str, str]],
    sender_name: str = "Parth",
    email_index: int = 0,  # Which email in the sequence to draft (0 = first email)
) -> dict[str, Any]:
    """
    Create Gmail drafts for each lead's outreach email.

    Args:
        leads: List of prospect dicts
        sender_name: Your name for the email signature
        email_index: Which email in the 5-step sequence to draft (0-4)

    Returns stats dict.
    """
    if not leads:
        return {"drafted": 0, "failed": 0, "skipped": 0, "total": 0}

    if not OUTREACH_GMAIL_USER or not OUTREACH_GMAIL_APP_PASSWORD:
        log.error("Outreach Gmail credentials not set. Skipping drafts.")
        return {"drafted": 0, "failed": len(leads), "skipped": 0, "total": len(leads)}

    log.info("Creating outreach drafts (Email %d of sequence) for %d leads...",
             email_index + 1, len(leads))

    drafted = 0
    failed = 0
    skipped = 0
    failed_leads = []

    for i, lead in enumerate(leads, 1):
        biz_name = lead.get("business_name", "Unknown")
        to_email = lead.get("email", "")

        if not to_email or "@" not in to_email:
            log.info("[%d/%d] Skipping %s — no email", i, len(leads), biz_name)
            skipped += 1
            continue

        # Generate the sequence and pick the right email
        sequence = generate_outreach_sequence(lead, sender_name)
        if email_index >= len(sequence):
            log.warning("Email index %d out of range for %s", email_index, biz_name)
            failed += 1
            continue

        email_data = sequence[email_index]

        success = _create_gmail_draft(
            to_email=to_email,
            subject=email_data["subject"],
            body_text=email_data["body"],
        )

        if success:
            log.info("[%d/%d] Draft created: %s <%s>", i, len(leads), biz_name, to_email)
            drafted += 1
        else:
            log.warning("[%d/%d] Draft FAILED: %s <%s>", i, len(leads), biz_name, to_email)
            failed += 1
            failed_leads.append(lead)

        if i < len(leads):
            time.sleep(2)  # Rate limit IMAP operations

    log.info("Draft results: %d drafted, %d failed, %d skipped", drafted, failed, skipped)

    # Send notification with results
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        _send_draft_notification(drafted, failed, skipped, len(leads), failed_leads)

    return {
        "drafted": drafted,
        "failed": failed,
        "skipped": skipped,
        "total": len(leads),
    }


def _send_draft_notification(
    drafted: int, failed: int, skipped: int, total: int,
    failed_leads: list[dict[str, str]],
) -> bool:
    """Send a notification email with draft creation results."""
    today_str = date.today().strftime("%B %d, %Y")

    # Build failed leads rows
    failed_rows = ""
    for i, lead in enumerate(failed_leads, 1):
        failed_rows += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #222;color:#FFF;font-size:13px;">{lead.get('business_name', '—')}</td>
            <td style="padding:10px;border-bottom:1px solid #222;color:#AAA;font-size:13px;">{lead.get('city', '—')}</td>
            <td style="padding:10px;border-bottom:1px solid #222;color:#AAA;font-size:13px;">{lead.get('niche', '—')}</td>
            <td style="padding:10px;border-bottom:1px solid #222;color:#AAA;font-size:13px;">{lead.get('email', '—')}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:40px 20px;background:#050505;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" style="max-width:650px;margin:0 auto;background:#0A0A0A;border:1px solid #1A1A1A;border-radius:12px;overflow:hidden;">
    <tr><td style="padding:30px;border-bottom:1px solid #1A1A1A;text-align:center;">
        <div style="letter-spacing:2px;font-size:11px;color:#D4AF37;font-weight:700;margin-bottom:8px;">LOCALOS OUTREACH REPORT</div>
        <h1 style="margin:0;font-size:22px;color:#FFF;font-weight:300;">{today_str}</h1>
    </td></tr>
    <tr><td style="padding:20px 30px;">
        <table width="100%" style="background:#111;border:1px solid #222;border-radius:8px;">
            <tr>
                <td style="padding:16px;text-align:center;border-right:1px solid #222;">
                    <div style="font-size:28px;color:#D4AF37;">{drafted}</div>
                    <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">Drafted</div>
                </td>
                <td style="padding:16px;text-align:center;border-right:1px solid #222;">
                    <div style="font-size:28px;color:#FF6B6B;">{failed}</div>
                    <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">Failed</div>
                </td>
                <td style="padding:16px;text-align:center;border-right:1px solid #222;">
                    <div style="font-size:28px;color:#666;">{skipped}</div>
                    <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">No Email</div>
                </td>
                <td style="padding:16px;text-align:center;">
                    <div style="font-size:28px;color:#FFF;">{total}</div>
                    <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">Total</div>
                </td>
            </tr>
        </table>
    </td></tr>
    {"" if not failed_leads else f'''
    <tr><td style="padding:0 30px 20px;">
        <h3 style="color:#FF6B6B;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Failed Drafts</h3>
        <table width="100%" style="border-collapse:collapse;">
            <thead><tr>
                <th style="padding:8px;border-bottom:1px solid #333;color:#666;font-size:10px;text-transform:uppercase;text-align:left;">Business</th>
                <th style="padding:8px;border-bottom:1px solid #333;color:#666;font-size:10px;text-transform:uppercase;text-align:left;">City</th>
                <th style="padding:8px;border-bottom:1px solid #333;color:#666;font-size:10px;text-transform:uppercase;text-align:left;">Niche</th>
                <th style="padding:8px;border-bottom:1px solid #333;color:#666;font-size:10px;text-transform:uppercase;text-align:left;">Email</th>
            </tr></thead>
            <tbody>{failed_rows}</tbody>
        </table>
    </td></tr>
    '''}
    <tr><td style="padding:16px 30px;background:#050505;text-align:center;">
        <p style="margin:0;color:#444;font-size:10px;text-transform:uppercase;letter-spacing:1px;">
            Drafts ready in {OUTREACH_GMAIL_USER or 'your outreach inbox'}
        </p>
    </td></tr>
</table>
</body></html>"""

    subject = f"LOCALOS Outreach — {today_str} — {drafted} Drafts Created"

    msg = MIMEMultipart("mixed")
    msg["From"] = f"LOCALOS Bot <{GMAIL_USER}>"
    msg["To"] = NOTIFICATION_RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=60) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, NOTIFICATION_RECIPIENT, msg.as_string())
        log.info("Notification sent to %s", NOTIFICATION_RECIPIENT)
        return True
    except Exception as exc:
        log.error("Notification send failed: %s", exc)
        return False
