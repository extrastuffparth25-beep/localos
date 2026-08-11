"""
linkedin_scripts.py — LinkedIn Outreach Scripts for LOCALOS.

Step-by-step LinkedIn outreach flow:
  1. Connection request (with personalized note)
  2. First DM after connection accepted
  3. Follow-up DM with value
  4. Close DM with booking link

All designed to sound natural and conversational.
"""

from __future__ import annotations


def generate_linkedin_sequence(
    business_name: str,
    first_name: str,
    city: str,
    niche: str,
    sender_name: str = "Parth",
    booking_link: str = "https://cal.com/localos",
) -> list[dict[str, str]]:
    """
    Generate a LinkedIn outreach sequence.
    Returns a list of dicts with: step, day_offset, message, notes.
    """

    return [
        # ── Step 1: Connection Request ──
        {
            "step": "connection_request",
            "day_offset": 0,
            "message": f"""Hey {first_name}, I noticed {business_name} in {city} — looks like you're doing great work in the {niche.lower()} space. Would love to connect!""",
            "notes": "LinkedIn connection notes are limited to 300 characters. Keep it short and genuine. Don't sell in the connection request.",
        },

        # ── Step 2: First DM (after they accept) ──
        {
            "step": "first_dm",
            "day_offset": 1,
            "message": f"""Thanks for connecting, {first_name}! 🙌

I've been working with {niche.lower()} businesses on something pretty interesting — helping them rank in the top 3 on Google Maps.

It's one of those things where most business owners don't realize how much revenue they're leaving on the table. 60% of all Google Maps clicks go to the top 3 results, and most local businesses aren't even close.

I'm curious — have you ever looked into how {business_name} ranks on Google Maps for your main keywords?

Not trying to pitch you anything, genuinely curious since I work in this space.""",
            "notes": "Wait at least 24 hours after they accept your connection before sending. Don't sell — just start a conversation.",
        },

        # ── Step 3: Value DM ──
        {
            "step": "value_dm",
            "day_offset": 4,
            "message": f"""Hey {first_name}, hope you don't mind me following up.

I actually took a look at {business_name}'s Google Maps presence out of curiosity. A few things I noticed:

• You're not showing up in the top 3 for "{niche.lower()} in {city}"
• Your competitors seem to have more recent posts and reviews
• There are some quick optimization wins that could help

I do this stuff for a living so I tend to notice these things lol.

If you're interested, I could put together a free audit — takes about 5 minutes and shows you exactly where you stand vs. your competitors.

No strings attached, just thought it might be useful.""",
            "notes": "Only send this if they didn't respond to the first DM. If they responded positively, skip to closing.",
        },

        # ── Step 4: Close DM ──
        {
            "step": "close_dm",
            "day_offset": 7,
            "message": f"""Hey {first_name}, last message from me on this — promise 😄

Just wanted to share that we recently helped a {niche.lower()} business go from page 2 to #1 on Google Maps in about 2 weeks. Their calls from Google went up by about 3x.

If you ever want to explore something similar for {business_name}, I'm always happy to chat. Here's my calendar if you want to grab a quick 10-min call:

{booking_link}

Either way, great connecting with you! 🤝""",
            "notes": "This is your final message. If no response, move on. Don't be pushy on LinkedIn — it damages your professional brand.",
        },
    ]


def format_linkedin_playbook(
    business_name: str,
    first_name: str,
    city: str,
    niche: str,
    sender_name: str = "Parth",
) -> str:
    """
    Format the LinkedIn sequence as a readable playbook.
    """
    sequence = generate_linkedin_sequence(
        business_name, first_name, city, niche, sender_name
    )

    lines = []
    lines.append(f"{'═' * 60}")
    lines.append(f"🔗 LINKEDIN OUTREACH PLAYBOOK")
    lines.append(f"   Target: {business_name} ({first_name})")
    lines.append(f"   Location: {city} | Industry: {niche}")
    lines.append(f"{'═' * 60}")

    for i, step in enumerate(sequence, 1):
        lines.append(f"\n{'─' * 50}")
        lines.append(f"📌 STEP {i}: {step['step'].upper().replace('_', ' ')}")
        lines.append(f"📅 Day: {step['day_offset']}")
        lines.append(f"{'─' * 50}")
        lines.append(f"\n{step['message']}")
        lines.append(f"\n💡 Note: {step['notes']}")

    lines.append(f"\n{'═' * 60}\n")
    return "\n".join(lines)
