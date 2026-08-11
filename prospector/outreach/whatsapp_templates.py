"""
whatsapp_templates.py — WhatsApp Business Message Templates for LOCALOS.

Pre-written templates designed for WhatsApp outreach to local businesses.
These are meant to be sent manually through WhatsApp Business app.

Each template sounds natural, conversational, and avoids sounding salesy.
"""

from __future__ import annotations


def generate_whatsapp_sequence(
    business_name: str,
    first_name: str,
    city: str,
    niche: str,
    sender_name: str = "Parth",
    booking_link: str = "https://cal.com/localos",
) -> list[dict[str, str]]:
    """
    Generate a WhatsApp outreach sequence for a single prospect.
    Returns a list of dicts with: step, day_offset, message.
    """

    return [
        # ── Message 1: Initial Contact ──
        {
            "step": "initial_contact",
            "day_offset": 0,
            "message": f"""Hey {first_name} 👋

I came across {business_name} while looking at {niche} businesses in {city} on Google Maps.

Quick question — have you noticed that your listing isn't showing in the top 3 results when people search "{niche} near {city}"?

I help local businesses fix this. Most of my clients see results in about 2 weeks.

Would you be open to a quick free audit of your listing? Takes 5 mins and it'll show you exactly what's holding you back.

— {sender_name}""",
        },

        # ── Message 2: Follow-up (if no response) ──
        {
            "step": "follow_up",
            "day_offset": 3,
            "message": f"""Hey {first_name}, just following up on my last message.

I actually went ahead and checked {business_name}'s Google Maps data. Here's what I noticed:

📊 You're not in the top 3 for your main keywords
📊 Your competitors have more recent Google Posts
📊 A few quick fixes could make a big difference

I genuinely think you're leaving money on the table here. 60% of all clicks go to the top 3 — if you're not there, those customers are going to someone else.

Want me to send over the full breakdown? No charge, no pitch — just data.

— {sender_name}""",
        },

        # ── Message 3: After Interest ──
        {
            "step": "after_interest",
            "day_offset": None,  # Send when they respond positively
            "message": f"""Awesome, glad you're interested! 🙌

So here's the quick version of what we do:

1️⃣ We optimize your Google Business Profile (keywords, categories, description)
2️⃣ Our AI posts weekly updates to your listing automatically
3️⃣ We respond to all your Google reviews professionally
4️⃣ We track your ranking and send you monthly reports

Most clients see a jump from page 2 to top 3 within 14 days.

It's $499/month, month-to-month, cancel anytime. No contracts.

Want to hop on a quick 10-min call so I can show you what the dashboard looks like?

📅 {booking_link}

— {sender_name}""",
        },

        # ── Message 4: Objection Handling — "Too expensive" ──
        {
            "step": "objection_price",
            "day_offset": None,
            "message": f"""Totally understand, {first_name}. It's a fair question.

Here's how I think about it:

Most {niche} businesses in {city} that rank in the top 3 get 15-30 extra calls per month from Google Maps alone.

If even 20% of those become paying customers, that's probably $2,000-$5,000+ in revenue from a $499/month investment.

Compare that to Google Ads where you'd spend $2,000-$4,000/month for similar results — and the moment you stop paying for ads, you disappear.

With us, the optimization sticks. And if you don't see results in 30 days, you can cancel. No questions asked.

Want to try it out for just one month and see what happens?

— {sender_name}""",
        },

        # ── Message 5: Objection Handling — "I need to think about it" ──
        {
            "step": "objection_think",
            "day_offset": None,
            "message": f"""No rush at all, {first_name}. Take your time.

Just one thing to keep in mind — we only work with 3 {niche} businesses per city. Once we take on a client, we can't work with their direct competitors.

So if one of your competitors signs up first, we won't be able to work with {business_name} in that area.

No pressure though. When you're ready, just shoot me a message. The offer for a free audit is always open 👍

— {sender_name}""",
        },
    ]


def format_for_copy(messages: list[dict[str, str]]) -> str:
    """
    Format all WhatsApp messages for easy copy-paste.
    Returns a formatted string.
    """
    lines = []
    for msg in messages:
        lines.append(f"{'═' * 50}")
        lines.append(f"📱 STEP: {msg['step'].upper().replace('_', ' ')}")
        if msg['day_offset'] is not None:
            lines.append(f"📅 Send on: Day {msg['day_offset']}")
        else:
            lines.append(f"📅 Send when: Triggered by response")
        lines.append(f"{'═' * 50}")
        lines.append(msg["message"])
        lines.append("")
    return "\n".join(lines)
