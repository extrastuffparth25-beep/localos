"""
drip_engine.py — Drip Campaign & Follow-up logic for LOCALOS.

Determines which leads need follow-ups based on the sequence step
and the number of days since last contact.
"""

from datetime import datetime, date
import logging

log = logging.getLogger(__name__)

# Days to wait between emails:
# Email 1 -> (wait 3 days) -> Email 2
# Email 2 -> (wait 4 days) -> Email 3
# Email 3 -> (wait 7 days) -> Email 4
# Email 4 -> (wait 14 days) -> Email 5 (Breakup)
FOLLOW_UP_DELAYS = {
    0: 3,   # Wait 3 days after Email 1
    1: 4,   # Wait 4 days after Email 2
    2: 7,   # Wait 7 days after Email 3
    3: 14,  # Wait 14 days after Email 4
}

def get_due_followups(leads: list[dict[str, str]]) -> dict[int, list[dict[str, str]]]:
    """
    Returns a dictionary mapping email_index to a list of leads that are due for that email.
    Skips leads that have 'status' != 'Contacted'.
    """
    due_leads = {1: [], 2: [], 3: [], 4: []}
    today = date.today()

    for lead in leads:
        status = lead.get("status", "New")
        if status != "Contacted":
            continue

        try:
            seq_step = int(lead.get("sequence_step", 0))
            last_date_str = lead.get("last_contact_date", "")
            if not last_date_str:
                continue
                
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            days_passed = (today - last_date).days
            
            if seq_step in FOLLOW_UP_DELAYS:
                required_delay = FOLLOW_UP_DELAYS[seq_step]
                if days_passed >= required_delay:
                    next_step = seq_step + 1
                    if next_step <= 4:
                        due_leads[next_step].append(lead)
                        log.info("Lead %s due for Email %d (Days passed: %d, Required: %d)", 
                                 lead.get("business_name"), next_step + 1, days_passed, required_delay)
        except Exception as e:
            log.warning("Error calculating follow-up for lead %s: %s", lead.get("email"), str(e))
            
    return due_leads
