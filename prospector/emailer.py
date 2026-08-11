"""
emailer.py — Premium HTML Email Digest Sender for LOCALOS Prospector.

Sends a daily digest of new prospects with their scores, tiers, and
contact info — all in a stunning dark-themed email.
"""

from __future__ import annotations

import csv
import io
import logging
import smtplib
import time
from datetime import date
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from typing import Any

from config import (
    CSV_FIELDNAMES,
    GMAIL_APP_PASSWORD,
    GMAIL_SMTP_HOST,
    GMAIL_SMTP_PORT,
    GMAIL_USER,
    RECIPIENT_EMAIL,
)

log = logging.getLogger(__name__)


def _tier_color(tier: str) -> str:
    """Get color for a score tier."""
    return {
        "A": "#22C55E",
        "B": "#D4AF37",
        "C": "#666666",
    }.get(tier, "#666666")


def _tier_label(tier: str) -> str:
    """Get label for a score tier."""
    return {
        "A": "🔥 HOT",
        "B": "🟡 WARM",
        "C": "❄️ COLD",
    }.get(tier, "❓")


def _build_html(leads: list[dict[str, str]], stats: dict[str, Any]) -> str:
    """Build the premium HTML email digest."""
    today_str = date.today().strftime("%B %d, %Y")

    # Count tiers
    tier_a = sum(1 for l in leads if l.get("tier") == "A")
    tier_b = sum(1 for l in leads if l.get("tier") == "B")
    tier_c = sum(1 for l in leads if l.get("tier") == "C")

    # Build lead rows
    lead_rows = ""
    for i, lead in enumerate(leads, 1):
        tier = lead.get("tier", "C")
        score = lead.get("score", "0")
        color = _tier_color(tier)
        label = _tier_label(tier)

        website = lead.get("website", "")
        website_link = (
            f'<a href="{website}" style="color:#D4AF37;text-decoration:none;font-size:12px;">Visit →</a>'
            if website
            else '<span style="color:#666;font-size:12px;">N/A</span>'
        )

        email = lead.get("email", "")
        email_display = (
            f'<a href="mailto:{email}" style="color:#AAA;text-decoration:none;font-size:12px;">{email}</a>'
            if "@" in email
            else f'<span style="color:#666;font-size:12px;">{email or "—"}</span>'
        )

        lead_rows += f"""
        <tr>
            <td style="padding:12px 10px;border-bottom:1px solid #1A1A1A;color:#FFF;font-size:14px;font-weight:600;">{lead.get('business_name', '—')}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #1A1A1A;color:#AAA;font-size:13px;">{lead.get('niche', '—')}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #1A1A1A;color:#AAA;font-size:13px;">{lead.get('city', '—')}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #1A1A1A;text-align:center;">
                <span style="display:inline-block;padding:3px 10px;border-radius:100px;font-size:11px;font-weight:700;color:{color};background:rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4))},0.1);border:1px solid rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0, 2, 4))},0.3);">{label} ({score})</span>
            </td>
            <td style="padding:12px 10px;border-bottom:1px solid #1A1A1A;">{email_display}</td>
            <td style="padding:12px 10px;border-bottom:1px solid #1A1A1A;">{website_link}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:40px 20px;background-color:#050505;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',sans-serif;line-height:1.5;">

<table width="100%" cellpadding="0" cellspacing="0" style="max-width:800px;margin:0 auto;background-color:#0A0A0A;border:1px solid #1A1A1A;border-radius:12px;overflow:hidden;">

    <!-- Header -->
    <tr>
        <td style="padding:30px 40px;border-bottom:1px solid #1A1A1A;text-align:center;">
            <div style="text-transform:uppercase;letter-spacing:3px;font-size:11px;color:#D4AF37;font-weight:700;margin-bottom:8px;">LOCALOS Daily Prospect Digest</div>
            <h1 style="margin:0 0 6px;font-size:24px;color:#FFFFFF;font-weight:300;">{today_str}</h1>
            <p style="margin:0;color:#666;font-size:13px;">{len(leads)} new prospects found • {stats.get('elapsed', '—')} runtime</p>
        </td>
    </tr>

    <!-- Stats Bar -->
    <tr>
        <td style="padding:0 40px;">
            <table width="100%" style="margin:20px 0;background:#111;border:1px solid #222;border-radius:8px;">
                <tr>
                    <td style="padding:16px;text-align:center;border-right:1px solid #222;">
                        <div style="font-size:30px;color:#22C55E;font-weight:400;">{tier_a}</div>
                        <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">🔥 Tier A</div>
                    </td>
                    <td style="padding:16px;text-align:center;border-right:1px solid #222;">
                        <div style="font-size:30px;color:#D4AF37;font-weight:400;">{tier_b}</div>
                        <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">🟡 Tier B</div>
                    </td>
                    <td style="padding:16px;text-align:center;border-right:1px solid #222;">
                        <div style="font-size:30px;color:#666;font-weight:400;">{tier_c}</div>
                        <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">❄️ Tier C</div>
                    </td>
                    <td style="padding:16px;text-align:center;">
                        <div style="font-size:30px;color:#FFF;font-weight:300;">{stats.get('sources_tried', 0)}</div>
                        <div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">Sources</div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- Leads Table -->
    <tr>
        <td style="padding:0 40px 30px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <thead>
                    <tr>
                        <th style="padding:0 10px 10px;border-bottom:1px solid #333;color:#666;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;text-align:left;">Business</th>
                        <th style="padding:0 10px 10px;border-bottom:1px solid #333;color:#666;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;text-align:left;">Niche</th>
                        <th style="padding:0 10px 10px;border-bottom:1px solid #333;color:#666;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;text-align:left;">City</th>
                        <th style="padding:0 10px 10px;border-bottom:1px solid #333;color:#666;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;text-align:center;">Score</th>
                        <th style="padding:0 10px 10px;border-bottom:1px solid #333;color:#666;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;text-align:left;">Email</th>
                        <th style="padding:0 10px 10px;border-bottom:1px solid #333;color:#666;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;text-align:left;">Website</th>
                    </tr>
                </thead>
                <tbody>{lead_rows}</tbody>
            </table>
        </td>
    </tr>

    <!-- Footer -->
    <tr>
        <td style="padding:20px 40px;background:#050505;text-align:center;">
            <p style="margin:0;color:#444;font-size:11px;text-transform:uppercase;letter-spacing:1px;">
                LOCALOS Prospect Engine • Automated Daily
            </p>
        </td>
    </tr>
</table>

</body>
</html>"""

    return html


def _build_csv_attachment(leads: list[dict[str, str]]) -> MIMEBase:
    """Build a CSV file attachment from leads data."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(leads)

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(output.getvalue().encode("utf-8"))
    encoders.encode_base64(attachment)

    today = date.today().strftime("%Y-%m-%d")
    attachment.add_header(
        "Content-Disposition",
        f'attachment; filename="localos_prospects_{today}.csv"',
    )
    return attachment


def send_digest(
    leads: list[dict[str, str]],
    stats: dict[str, Any],
    dry_run: bool = False,
) -> bool:
    """
    Send the daily prospect digest email.

    Args:
        leads: List of scored prospect dicts
        stats: Pipeline stats dict
        dry_run: If True, print HTML to stdout instead of sending
    """
    if not leads:
        log.info("No leads to send digest for.")
        return True

    html = _build_html(leads, stats)

    if dry_run:
        print(html)
        return True

    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        log.error("GMAIL_USER or GMAIL_APP_PASSWORD not set.")
        return False

    today_str = date.today().strftime("%B %d, %Y")
    tier_a = sum(1 for l in leads if l.get("tier") == "A")

    subject = f"LOCALOS Prospects — {today_str} — {len(leads)} Leads ({tier_a} Hot)"

    msg = MIMEMultipart("mixed")
    msg["From"] = f"LOCALOS Bot <{GMAIL_USER}>"
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject
    msg["Reply-To"] = GMAIL_USER
    msg.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(_build_csv_attachment(leads))

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            log.info("Sending digest (attempt %d/%d) ...", attempt, max_attempts)
            with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=60) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
            log.info("Digest sent successfully to %s", RECIPIENT_EMAIL)
            return True
        except smtplib.SMTPAuthenticationError as exc:
            log.error("SMTP Auth error: %s", exc)
            return False
        except (smtplib.SMTPException, OSError) as exc:
            log.error("SMTP error (attempt %d/%d): %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                time.sleep(attempt * 10)

    log.error("All digest send attempts failed.")
    return False
