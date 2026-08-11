"""
main.py — LOCALOS Fully Autonomous AI Agency Orchestrator.

Sequence:
    1. Load existing prospects from CSV
    2. Inbox Scan: Check for replies via IMAP
    3. AI Closer: Handle replies and close deals (WhatsApp alert on Win)
    4. Drip Engine: Send sequence follow-ups to non-responders
    5. Prospecting: Find, score, and send Email 1 to new leads
    6. Update & Persist CSV
    7. Send daily digest email
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import sys
import shutil
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import Any

from config import CSV_FIELDNAMES, LEADS_CSV
from prospector import prospect_leads
from scorer import score_leads_batch
from emailer import send_digest
from sender import send_outreach_emails, _send_outreach_email
from inbox_scanner import scan_for_replies
from ai_closer import generate_expert_reply
from drip_engine import get_due_followups
from closing_alert import alert_client_closed
from bounce_detector import extract_bounced_email

# ──────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────
_stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-14s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(_stream)],
)
log = logging.getLogger("localos")

def load_existing_prospects(csv_path: str) -> list[dict[str, str]]:
    path = Path(csv_path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_prospects_to_csv(csv_path: str, leads: list[dict[str, str]]) -> None:
    path = Path(csv_path)
    
    # Atomic write: Write to temp file first, then replace
    temp_path = path.with_suffix(".tmp.csv")
    backup_path = path.with_suffix(".backup.csv")
    
    try:
        # Create backup if exists
        if path.exists():
            shutil.copy2(path, backup_path)
            
        with temp_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(leads)
            
        # Atomic replace
        temp_path.replace(path)
        log.info("CRM data safely saved using atomic write.")
    except Exception as e:
        log.error("CRITICAL: Failed to save CRM data: %s", str(e))
        if temp_path.exists():
            temp_path.unlink()

def main() -> None:
    parser = argparse.ArgumentParser(description="LOCALOS — AI Agency Orchestrator")
    parser.add_argument("--skip-prospecting", action="store_true")
    args = parser.parse_args()

    log.info("=" * 65)
    log.info("LOCALOS — Waking up AI Employee...")
    log.info("=" * 65)

    stats: dict[str, Any] = {
        "sources_tried": 0, "candidates_found": 0, "duplicates_filtered": 0,
        "leads_accepted": 0, "cities_searched": [], "start_time": datetime.now(),
        "elapsed": "", "replies_handled": 0, "followups_sent": 0, "new_emails_sent": 0,
        "deals_closed": 0
    }

    # 1. Load State
    leads = load_existing_prospects(LEADS_CSV)
    leads_dict = {l.get("email", "").lower(): l for l in leads if l.get("email")}

    # 2 & 3. Inbox Scan & AI Closer
    log.info("-" * 45)
    log.info("Step 1: Checking Inbox, Auto-Responders, and Bounces...")
    prospect_emails = list(leads_dict.keys())
    replies, bounces = scan_for_replies(prospect_emails)
    
    # Process Bounces
    if bounces:
        log.info("Processing %d potential bounce notices...", len(bounces))
        for bounce in bounces:
            bounced_email = extract_bounced_email(bounce["subject"], bounce["body"])
            if bounced_email and bounced_email in leads_dict:
                log.warning("🚨 BOUNCE DETECTED: %s. Marking as Bounced to protect sender score.", bounced_email)
                leads_dict[bounced_email]["status"] = "Bounced"
    
    for reply in replies:
        sender = reply["email"]
        lead = leads_dict.get(sender)
        if not lead:
            continue
            
        biz_name = lead.get("business_name", "Unknown")
        log.info("Processing reply from %s...", biz_name)
        
        # Append to conversation history
        history = lead.get("conversation_history", "")
        history += f"\n\nCLIENT ({date.today()}): {reply['body']}"
        
        # Ask Gemini to handle it
        expert_response, status_intent, next_steps = generate_expert_reply(
            biz_name, lead.get("niche", ""), lead.get("city", ""), history, reply['body']
        )
        
        history += f"\n\nAI ({date.today()}): {expert_response}"
        lead["conversation_history"] = history
        
        # Send the AI response back
        _send_outreach_email(sender, f"Re: {reply['subject']}", expert_response)
        stats["replies_handled"] += 1
        
        # Handle the sentiment
        if status_intent == "NOT_INTERESTED":
            lead["status"] = "Lost"
            log.info("%s is NOT INTERESTED. Marking as Lost.", biz_name)
        elif status_intent == "CLOSED":
            lead["status"] = "Won"
            stats["deals_closed"] += 1
            log.info("🎉 %s CLOSED! Sending WhatsApp Alert...", biz_name)
            alert_client_closed(biz_name, sender, history[-300:], next_steps)
        else:
            lead["status"] = "Replied"
            log.info("%s is INTERESTED. AI handled the objection.", biz_name)

    # 4. Drip Engine (Follow-ups)
    log.info("-" * 45)
    log.info("Step 2: Processing Drip Campaign Follow-ups...")
    due_followups = get_due_followups(leads)
    
    for step, due_leads in due_followups.items():
        if not due_leads:
            continue
        log.info("Sending Email #%d to %d leads...", step + 1, len(due_leads))
        send_stats = send_outreach_emails(due_leads, email_index=step)
        stats["followups_sent"] += send_stats["sent"]
        
        # Update sequence step and date
        for lead in due_leads:
            lead["sequence_step"] = str(step)
            lead["last_contact_date"] = str(date.today())

    # 5. Prospecting & First Emails
    if not args.skip_prospecting:
        log.info("-" * 45)
        log.info("Step 3: Prospecting New Leads...")
        new_leads = prospect_leads(leads, stats)
        
        if new_leads:
            scored_leads = score_leads_batch(new_leads)
            scored_leads.sort(key=lambda x: int(x.get("score", 0)), reverse=True)
            
            sendable = [l for l in scored_leads if l.get("tier") in ("A", "B")]
            if sendable:
                log.info("Sending Email #1 to %d Hot/Warm new leads...", len(sendable))
                first_email_stats = send_outreach_emails(sendable, email_index=0)
                stats["new_emails_sent"] = first_email_stats["sent"]
                
                # Update status of those we emailed
                for l in sendable:
                    l["status"] = "Contacted"
                    l["sequence_step"] = "0"
                    l["last_contact_date"] = str(date.today())
            
            leads.extend(scored_leads)
    else:
        log.info("Skipping prospecting step.")

    # Calculate elapsed time
    elapsed_delta = datetime.now() - stats["start_time"]
    minutes, seconds = divmod(int(elapsed_delta.total_seconds()), 60)
    stats["elapsed"] = f"{minutes}m {seconds}s"

    # 6. Save State
    log.info("-" * 45)
    log.info("Step 4: Saving State...")
    save_prospects_to_csv(LEADS_CSV, leads)

    # 7. Send Digest
    log.info("-" * 45)
    log.info("Step 5: Sending Daily Report...")
    # Update digest logic if needed, but standard one works
    send_digest(leads[-stats["leads_accepted"]:], stats)

    log.info("=" * 65)
    log.info("Day Complete. %d New Emails, %d Follow-ups, %d Replies Handled, %d Deals Closed.", 
             stats["new_emails_sent"], stats["followups_sent"], stats["replies_handled"], stats["deals_closed"])
    log.info("=" * 65)

if __name__ == "__main__":
    main()
