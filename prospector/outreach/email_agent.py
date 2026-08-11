"""
email_agent.py — AI-Powered Hyper-Personalized Outreach Engine.

Uses Gemini to perform a mini-audit of the prospect's Google Business Profile
and generates an incredibly specific, non-generic first email that proves
undeniable expertise and creates FOMO.
"""

import logging
import os
import random

try:
    import google.generativeai as genai
except ImportError:
    genai = None

log = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)

# Fallback sequence in case the AI fails or the API key is missing
FALLBACK_SEQUENCE = [
    {
        "subject": "Quick question about {business_name}",
        "body": "Hi there,\n\nI was searching for a {niche} in {city} and noticed {business_name} isn't showing up in the top 3 on Google Maps. You're losing a lot of calls to your competitors.\n\nI run a local SEO agency that strictly gets businesses into the top 3 on Maps, and I'd love to show you how I can do it for you completely risk-free for 14 days.\n\nAre you open to a quick 5-minute chat this week?\n\nBest,\n{sender_name}"
    },
    {
        "subject": "Re: Quick question about {business_name}",
        "body": "Hi,\n\nJust following up on my previous email. I specialize in getting {niche}s in {city} ranked in the top 3 on Google Maps so they get all the organic phone calls.\n\nIf you don't get results in 30 days, you don't pay me a dime. Are you currently taking on new clients?\n\nBest,\n{sender_name}"
    },
    {
        "subject": "Any thoughts?",
        "body": "Hi again,\n\nI know you're busy running {business_name}. I just wanted to bump this to the top of your inbox.\n\nI only take on two {niche}s in {city} at a time to avoid conflicts of interest, and I'd love for you to be one of them. Let me know if you're open to a brief call to see if it's a fit.\n\nBest,\n{sender_name}"
    },
    {
        "subject": "Google Maps for {business_name}",
        "body": "Hi,\n\nI haven't heard back, so I assume improving your Google Maps ranking isn't a priority right now, or you're already swamped with customers!\n\nIf anything changes and you want to dominate the {city} market, keep my info on hand.\n\nBest,\n{sender_name}"
    }
]

def _generate_ai_audit_email(lead: dict, sender_name: str) -> dict[str, str]:
    """Uses Gemini to write a hyper-personalized email based on prospect data."""
    if not GEMINI_API_KEY or not genai:
        return FALLBACK_SEQUENCE[0]
        
    biz_name = lead.get("business_name", "your business")
    niche = lead.get("niche", "business")
    city = lead.get("city", "your city")
    rating = lead.get("google_rating", "Unknown")
    reviews = lead.get("review_count", "Unknown")
    competitor = lead.get("top_competitor", "your biggest competitor")
    
    prompt = f"""
    You are an elite, highly-paid Local SEO expert writing a cold email to the owner of {biz_name}.
    They are a {niche} in {city}. 
    Their current Google rating is {rating} stars with {reviews} reviews.
    Their top competitor ranking #1 on Maps is {competitor}.
    
    Write an extremely short, punchy, cold email. 
    NO GREETING LIKE "I hope this finds you well". 
    NO FLUFF.
    
    Your goal is to point out exactly why they are losing to {competitor} (e.g. low reviews, not in top 3).
    Your offer: You will rank them in the top 3 on Google Maps. If they don't get more calls in 30 days, they don't pay.
    Call to action: Ask if they are open to a quick chat.
    
    Make it sound like a busy human typed it on an iPhone. DO NOT SOUND LIKE AI.
    
    Format your response EXACTLY like this:
    SUBJECT: [Your punchy subject line]
    BODY:
    [The email body]
    
    Sign off as:
    Best,
    {sender_name}
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt, generation_config={"temperature": 0.7})
        text = response.text.strip()
        
        subject = "Quick question"
        body = text
        
        if "SUBJECT:" in text and "BODY:" in text:
            parts = text.split("BODY:")
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip()
            
        return {"subject": subject, "body": body}
    except Exception as e:
        log.error("AI Email Generator failed: %s", str(e))
        return FALLBACK_SEQUENCE[0]


def generate_outreach_sequence(lead: dict[str, str], sender_name: str = "Parth") -> list[dict[str, str]]:
    """
    Generates the full 4-step sequence. 
    Email 1 is hyper-personalized via AI.
    Emails 2, 3, and 4 use the fallback templates to keep thread continuity.
    """
    
    # Generate the hyper-personalized first email
    first_email = _generate_ai_audit_email(lead, sender_name)
    
    # Use fallback templates for follow-ups, replacing placeholders
    sequence = [first_email]
    
    for template in FALLBACK_SEQUENCE[1:]:
        subject = template["subject"].format(
            business_name=lead.get("business_name", "your business"),
            niche=lead.get("niche", "business"),
            city=lead.get("city", "your city")
        )
        body = template["body"].format(
            business_name=lead.get("business_name", "your business"),
            niche=lead.get("niche", "business"),
            city=lead.get("city", "your city"),
            sender_name=sender_name
        )
        sequence.append({"subject": subject, "body": body})
        
    return sequence
