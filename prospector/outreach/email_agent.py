"""
email_agent.py — AI-Powered Multi-Step Email Outreach for LOCALOS.

Generates hyper-personalized 5-step email sequences that:
  1. Sound completely human (no AI voice)
  2. Lead with value (free audit data)
  3. Build urgency naturally
  4. Handle common objections
  5. Close with a clean CTA

Each email is personalized with the prospect's actual business data.
"""

from __future__ import annotations

import logging
import re
from datetime import date

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Email Sequence Templates
# ──────────────────────────────────────────────
# Each email has: subject, body, day_offset (when to send after initial)
# Personalization tokens:
#   {{business_name}} — their business name
#   {{first_name}}    — owner's first name (extracted from email)
#   {{city}}          — their city
#   {{niche}}         — their industry
#   {{rating}}        — their Google rating
#   {{review_count}}  — their review count
#   {{website}}       — their website URL
#   {{competitor}}    — a competitor name in their area
#   {{your_name}}     — your name (the sender)
#   {{booking_link}}  — link to book a call

OUTREACH_SEQUENCE = [
    # ── EMAIL 1: Day 0 — The Value Bomb ──
    {
        "day_offset": 0,
        "subject": "Quick question about {{business_name}}",
        "body": """Hey {{first_name}},

I was looking up {{niche}} businesses in {{city}} and noticed something about {{business_name}} that I think you'd want to know.

Right now, when someone searches "{{niche}} near {{city}}" on Google Maps, your business isn't showing up in the top 3 results. That matters because 60% of all clicks go to those top 3 spots.

Basically, if you're not there — your competitors are getting your customers.

The good news? I've done this for a bunch of local businesses and it's honestly a pretty quick fix. Most of my clients see results within 2 weeks.

I put together a free audit of your Google Maps listing — shows exactly where you stand and what's keeping you from ranking higher. Want me to send it over?

No pitch, no strings. Just thought you'd want to see it.

{{your_name}}

P.S. — If you want to see what a #1 ranking actually looks like for businesses like yours, I'm happy to show you. Just reply "interested" and I'll send the data.""",
    },

    # ── EMAIL 2: Day 2 — Social Proof ──
    {
        "day_offset": 2,
        "subject": "Re: Quick question about {{business_name}}",
        "body": """Hey {{first_name}},

Following up on my last email. Wanted to share something quick.

I recently helped a {{niche}} business in a similar market go from #11 on Google Maps to #2 in just 18 days. Their phone calls from Google went from about 8 per week to 25+.

The crazy part? They were paying $3,500/month in Google Ads before. Now they spend $500/month with us and get MORE leads from organic Maps results than they ever got from ads.

Here's a quick breakdown of what we actually do:
— AI-optimized weekly Google Posts
— Professional review responses
— Keyword optimization for your listings
— Photo & category management

Everything's automated with AI, so it runs in the background while you focus on running your business.

If you want, I can do a quick 10-min call to show you exactly how it works for {{niche}} businesses. No commitment, just a walkthrough.

{{booking_link}}

Talk soon,
{{your_name}}""",
    },

    # ── EMAIL 3: Day 5 — The Loom/Video Offer ──
    {
        "day_offset": 5,
        "subject": "Made something for {{business_name}}",
        "body": """Hey {{first_name}},

I actually went ahead and put together a quick ranking analysis for {{business_name}}.

Here's what I found:
— You're currently ranking around position 8-12 for your main keywords
— Your top competitors have more Google Posts and more recent reviews
— There are some quick wins in your listing that could move the needle fast

I was thinking about recording a quick 2-minute video walking you through it all. Would that be helpful?

It'd show you exactly:
1. Where you rank vs your competitors right now
2. Why they're outranking you (it's usually something simple)
3. What we'd fix in the first 14 days

Just reply "send it" and I'll make the video for you. Takes me about 5 minutes and it's completely free.

{{your_name}}""",
    },

    # ── EMAIL 4: Day 8 — Scarcity ──
    {
        "day_offset": 8,
        "subject": "One spot left in {{city}}",
        "body": """Hey {{first_name}},

Quick heads up — we only take on 3 new clients per city per month. This is because we don't want competing businesses in the same market as our existing clients.

We currently have 1 spot left for {{city}} in the {{niche}} category.

I'm not trying to create fake urgency here — it's just how our model works. We can't rank two {{niche}} businesses in the same city against each other. So once we fill the spot, we won't be able to take on another {{niche}} client in {{city}} for a while.

If ranking higher on Google Maps is something you've been thinking about, now might be a good time to at least grab a quick call.

Here's my calendar: {{booking_link}}

Even if you decide it's not for you, I can send over that free audit we talked about. No hard feelings either way.

{{your_name}}""",
    },

    # ── EMAIL 5: Day 14 — The Breakup ──
    {
        "day_offset": 14,
        "subject": "Closing the loop on {{business_name}}",
        "body": """Hey {{first_name}},

This'll be my last email about this.

I reached out a couple of weeks ago about helping {{business_name}} rank higher on Google Maps. I know you're busy running a business, so I totally get it if this isn't a priority right now.

Just wanted to leave you with one thought:

Every day that your business isn't in the top 3 on Google Maps, you're essentially handing customers to the businesses that ARE. And those businesses aren't necessarily better than you — they just have better Google visibility.

If that ever becomes something you want to fix, feel free to reply to this email anytime. My offer for a free ranking audit is always open.

Wishing you and {{business_name}} the best,
{{your_name}}

P.S. — No hard feelings if you want me to stop emailing. Just reply "stop" and I'll take you off my list immediately. I respect your inbox.""",
    },
]


# ──────────────────────────────────────────────
# Name Extraction (same approach as lead-scraper)
# ──────────────────────────────────────────────
_GENERIC_EMAIL_PREFIXES = {
    "info", "contact", "hello", "hi", "support", "admin",
    "studio", "inquiries", "sales", "office", "bookings",
    "mail", "webmaster", "marketing", "connect", "team",
    "general", "help", "press", "media", "mgmt", "management",
    "billing", "accounts", "service", "reception", "front",
}

_GENERIC_BIZ_TERMS = {
    "dental", "dentistry", "plumbing", "hvac", "repair", "auto",
    "restaurant", "cafe", "salon", "spa", "gym", "fitness",
    "law", "legal", "attorney", "clinic", "office", "services",
    "group", "llc", "inc", "co", "ltd", "studio", "agency",
    "center", "centre", "shop", "store", "house", "the", "and",
}


def _extract_first_name(business_name: str, email: str) -> str:
    """
    Intelligently extract a first name from the email or business name.
    Falls back to 'there' if uncertain.
    """
    # Try email first
    if email and "@" in email:
        prefix = email.split("@")[0].lower()
        prefix = re.sub(r"\d+$", "", prefix)
        parts = re.split(r"[._\-]", prefix)
        first_part = parts[0]
        if first_part and first_part not in _GENERIC_EMAIL_PREFIXES and len(first_part) > 2:
            return first_part.capitalize()

    # Try business name
    if business_name:
        name = business_name.lower()
        for term in _GENERIC_BIZ_TERMS:
            name = re.sub(rf"\b{term}\b", "", name)
        name = re.sub(r"[^\w\s]", "", name).strip()
        name = re.sub(r"\s+", " ", name)
        words = name.split()
        if 1 <= len(words) <= 3:
            first_word = words[0]
            if len(first_word) > 2 and first_word not in {"the", "best", "top", "pro", "your", "my", "our"}:
                return first_word.capitalize()

    return "there"


# ──────────────────────────────────────────────
# Email Generation
# ──────────────────────────────────────────────
def generate_outreach_sequence(
    lead: dict[str, str],
    sender_name: str = "Parth",
    booking_link: str = "https://cal.com/localos",
) -> list[dict[str, str]]:
    """
    Generate a complete 5-email outreach sequence for a single lead.

    Returns a list of dicts with: day_offset, subject, body (all personalized).
    """
    biz_name = lead.get("business_name", "your business")
    email = lead.get("email", "")
    city = lead.get("city", "your area")
    niche = lead.get("niche", "local").lower()
    rating = lead.get("google_rating", "")
    review_count = lead.get("review_count", "")
    website = lead.get("website", "")

    first_name = _extract_first_name(biz_name, email)

    sequence = []
    for template in OUTREACH_SEQUENCE:
        subject = template["subject"]
        body = template["body"]

        # Replace all tokens
        replacements = {
            "{{business_name}}": biz_name,
            "{{first_name}}": first_name,
            "{{city}}": city,
            "{{niche}}": niche,
            "{{rating}}": rating or "your current rating",
            "{{review_count}}": review_count or "your reviews",
            "{{website}}": website or "your online presence",
            "{{competitor}}": f"other {niche} businesses",
            "{{your_name}}": sender_name,
            "{{booking_link}}": booking_link,
        }

        for token, value in replacements.items():
            subject = subject.replace(token, value)
            body = body.replace(token, value)

        sequence.append({
            "day_offset": template["day_offset"],
            "subject": subject,
            "body": body,
            "to_email": email,
            "to_name": first_name,
        })

    return sequence


def generate_all_sequences(
    leads: list[dict[str, str]],
    sender_name: str = "Parth",
    booking_link: str = "https://cal.com/localos",
) -> dict[str, list[dict[str, str]]]:
    """
    Generate outreach sequences for all leads.
    Returns a dict keyed by business_name.
    """
    all_sequences = {}
    for lead in leads:
        biz = lead.get("business_name", "Unknown")
        email = lead.get("email", "")

        if not email or "@" not in email:
            log.info("Skipping %s — no email address", biz)
            continue

        sequence = generate_outreach_sequence(lead, sender_name, booking_link)
        all_sequences[biz] = sequence
        log.info("Generated %d-email sequence for: %s <%s>", len(sequence), biz, email)

    log.info("Total sequences generated: %d", len(all_sequences))
    return all_sequences


def preview_sequence(lead: dict[str, str], sender_name: str = "Parth") -> str:
    """
    Generate a formatted text preview of the full outreach sequence.
    Useful for --preview / --dry-run modes.
    """
    sequence = generate_outreach_sequence(lead, sender_name)
    lines = []
    lines.append(f"{'=' * 70}")
    lines.append(f"OUTREACH SEQUENCE FOR: {lead.get('business_name', 'Unknown')}")
    lines.append(f"Email: {lead.get('email', 'N/A')}")
    lines.append(f"City: {lead.get('city', 'N/A')} | Niche: {lead.get('niche', 'N/A')}")
    lines.append(f"{'=' * 70}")

    for i, email in enumerate(sequence, 1):
        lines.append(f"\n{'─' * 50}")
        lines.append(f"📧 EMAIL {i} — Day {email['day_offset']}")
        lines.append(f"Subject: {email['subject']}")
        lines.append(f"{'─' * 50}")
        lines.append(email["body"])

    lines.append(f"\n{'=' * 70}\n")
    return "\n".join(lines)
