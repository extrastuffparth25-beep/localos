"""
main.py — LOCALOS Prospector Pipeline Orchestrator.

Sequence:
    1. Load existing prospects from CSV
    2. Run multi-source prospector
    3. Score and tier all new leads
    4. Append to CSV
    5. Create outreach drafts in Gmail
    6. Send the daily digest email
    7. Log final stats
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from config import CSV_FIELDNAMES, LEADS_CSV
from prospector import prospect_leads
from scorer import score_leads_batch
from emailer import send_digest
from sender import send_outreach_emails

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


# ──────────────────────────────────────────────
# CSV Persistence
# ──────────────────────────────────────────────
def load_existing_prospects(csv_path: str) -> list[dict[str, str]]:
    """Load all existing prospects from the CSV file."""
    path = Path(csv_path)
    if not path.exists():
        log.info("No existing prospects file found. Starting fresh.")
        return []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    log.info("Loaded %d existing prospects from %s", len(leads), csv_path)
    return leads


def append_prospects_to_csv(csv_path: str, new_leads: list[dict[str, str]]) -> None:
    """Append new prospects to the CSV file."""
    path = Path(csv_path)
    file_exists = path.exists() and path.stat().st_size > 0

    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_leads)

    log.info("Appended %d new prospects to %s", len(new_leads), csv_path)


# ──────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="LOCALOS — Lead Prospector Pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the HTML digest to stdout instead of sending via SMTP.",
    )
    parser.add_argument(
        "--preview-outreach",
        action="store_true",
        help="Preview outreach email sequences for found leads.",
    )
    parser.add_argument(
        "--niches",
        nargs="+",
        help="Limit prospecting to specific niches (e.g., Dentist Plumber)",
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="Limit prospecting to specific cities (e.g., 'Dallas TX' 'Miami FL')",
    )
    parser.add_argument(
        "--skip-sending",
        action="store_true",
        help="Skip sending autonomous outreach emails.",
    )
    args = parser.parse_args()

    log.info("=" * 65)
    log.info("LOCALOS Prospector — Starting daily pipeline")
    log.info("=" * 65)

    stats: dict[str, Any] = {
        "sources_tried": 0,
        "candidates_found": 0,
        "duplicates_filtered": 0,
        "leads_accepted": 0,
        "cities_searched": [],
        "start_time": datetime.now(),
        "elapsed": "",
    }

    # Step 1: Load existing prospects
    existing = load_existing_prospects(LEADS_CSV)

    # Step 2: Prospect new leads
    log.info("-" * 45)
    log.info("Step 2: Prospecting new leads ...")
    new_leads = prospect_leads(
        existing, stats,
        target_niches=args.niches,
        target_cities=args.cities,
    )

    # Calculate elapsed time
    elapsed_delta = datetime.now() - stats["start_time"]
    minutes, seconds = divmod(int(elapsed_delta.total_seconds()), 60)
    stats["elapsed"] = f"{minutes}m {seconds}s"

    log.info("-" * 45)
    log.info("Prospecting complete in %s", stats["elapsed"])
    log.info("  Sources tried:       %d", stats["sources_tried"])
    log.info("  Candidates found:    %d", stats["candidates_found"])
    log.info("  Duplicates filtered: %d", stats["duplicates_filtered"])
    log.info("  New leads accepted:  %d", len(new_leads))
    log.info("  Cities searched:     %s", ", ".join(stats["cities_searched"]) or "--")

    if not new_leads:
        log.warning("No new leads found today. Skipping remaining steps.")
        return

    # Step 3: Score leads
    log.info("-" * 45)
    log.info("Step 3: Scoring %d leads ...", len(new_leads))
    scored_leads = score_leads_batch(new_leads)

    # Sort by score (highest first)
    scored_leads.sort(key=lambda x: int(x.get("score", 0)), reverse=True)

    tier_a = sum(1 for l in scored_leads if l.get("tier") == "A")
    tier_b = sum(1 for l in scored_leads if l.get("tier") == "B")
    tier_c = sum(1 for l in scored_leads if l.get("tier") == "C")
    log.info("  Tier A (HOT):  %d", tier_a)
    log.info("  Tier B (WARM): %d", tier_b)
    log.info("  Tier C (COLD): %d", tier_c)

    # Step 4: Persist to CSV
    log.info("-" * 45)
    log.info("Step 4: Saving %d prospects to %s ...", len(scored_leads), LEADS_CSV)
    append_prospects_to_csv(LEADS_CSV, scored_leads)

    # Step 5: Preview outreach (if requested)
    if args.preview_outreach:
        from outreach.email_agent import preview_sequence
        log.info("-" * 45)
        log.info("Step 5: Previewing outreach sequences ...")
        for lead in scored_leads[:3]:  # Preview first 3
            print(preview_sequence(lead))

    # Step 6: Send outreach emails autonomously
    if not args.dry_run and not args.skip_sending:
        log.info("-" * 45)
        log.info("Step 6: Autonomously sending outreach emails ...")
        # Only send for Tier A and B leads
        sendable = [l for l in scored_leads if l.get("tier") in ("A", "B")]
        if sendable:
            send_stats = send_outreach_emails(sendable, email_index=0)
            log.info("Sending: %d sent, %d failed, %d skipped",
                     send_stats["sent"], send_stats["failed"], send_stats["skipped"])
        else:
            log.info("No Tier A/B leads to send outreach to.")
    else:
        log.info("Skipping outreach sending (dry-run or --skip-sending).")

    # Step 7: Send digest email
    log.info("-" * 45)
    log.info("Step 7: Sending digest email ...")
    send_digest(scored_leads, stats, dry_run=args.dry_run)

    log.info("=" * 65)
    log.info("Pipeline complete — %d prospects found, %d Tier A (HOT)",
             len(scored_leads), tier_a)
    log.info("=" * 65)


if __name__ == "__main__":
    main()
