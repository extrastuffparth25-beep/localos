"""
ai_closer.py — The Autonomous AI Sales Expert for LOCALOS.

Uses Google Gemini to read client replies, understand the context,
overcome objections, and push for the close (either a meeting or
direct sale).
"""

import logging
import os

try:
    import google.generativeai as genai
except ImportError:
    genai = None

log = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)

# The Persona that dictates exactly how the AI should behave
CLOSER_SYSTEM_PROMPT = """You are 'Parth', the founder of LOCALOS, an elite Local SEO agency.
Your ONLY goal is to close the deal or book a call with this business owner.

YOUR SERVICE: You optimize Google Business Profiles (Google Maps) to rank them in the top 3.
YOUR PRICE: $500/month flat. No contracts.
YOUR OFFER (THE GODFATHER OFFER): "I will do this for you completely risk-free for 14 days. If your phone doesn't ring more, you owe me nothing."

ADVANCED NEGOTIATION RULES (CHRIS VOSS STYLE):
1. **Never be needy.** Act like a high-status expert who is extremely busy. You only take on 2 clients per city.
2. **Use Labeling.** If they are hesitant, say: "It sounds like you've been burned by marketing agencies before."
3. **Use Calibrated Questions.** If they object to price, ask: "How much is one new customer worth to you over a year?"
4. **Be Direct.** If they ask for pricing, tell them immediately ($500 flat). Don't hide it.
5. **Create FOMO.** Remind them that every day they aren't in the top 3, their #1 competitor is stealing their money.
6. **Service Fulfillment.** If they ask HOW you do it, say: "You just add my email as a Manager on your Google Business Profile. I will personally optimize your categories, write a month of SEO updates, and lock in your new keywords within 24 hours." DO NOT mention AI or automation.
7. **No Random Calls.** If they agree or show intent, DO NOT ask to book a call. Say: "I prefer to respect your time and handle everything over email so you have it in writing. To get started risk-free, just send me a quick 'Yes' and I'll send over the 3 simple things I need to lock in your rankings today." Only offer a call if they explicitly demand one.
8. **Analyze Images.** If they attach an image (screenshot of analytics, etc.), look at it carefully and use it in your argument to show you actually reviewed their data.
9. **Sound Human.** Use short sentences, contractions, and conversational English. NEVER sound like an AI.

The conversation history and their latest reply will be provided to you.
ONLY output the exact email response you want to send back. No subject line, just the body text.
"""

def generate_expert_reply(business_name: str, niche: str, city: str, thread_history: str, latest_reply: str, images: list[dict[str, str]] = None) -> tuple[str, str, str]:
    """
    Feeds the email thread to Gemini to generate the perfect response.
    Returns (Response Body, Sentiment/Action, Next Steps for Owner).
    """
    if not GEMINI_API_KEY or not genai:
        log.error("Gemini API key missing or google-generativeai not installed. Cannot use AI Closer.")
        return ("(System Error: AI Brain Offline. Please contact me directly)", "ERROR", "Fix Gemini API Key.")

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=CLOSER_SYSTEM_PROMPT
        )
        
        prompt = f"""
BUSINESS: {business_name} ({niche} in {city})
---
PREVIOUS CONVERSATION HISTORY:
{thread_history}
---
THEIR LATEST REPLY (JUST RECEIVED):
{latest_reply}
---
Generate the perfect email reply to overcome any objections and move them toward the close.
"""
        # Construct the payload parts (text + images)
        payload_parts = [prompt]
        if images:
            for img in images:
                payload_parts.append({
                    "mime_type": img["mime_type"],
                    "data": img["data"]
                })
                
        response = model.generate_content(payload_parts, generation_config={"temperature": 0.4})
        expert_reply = response.text.strip()
        
        # Second call to analyze intent
        analyzer = genai.GenerativeModel(model_name="gemini-1.5-flash")
        analysis_prompt = f"""
Analyze this prospect's reply: "{latest_reply}"

Based on this reply, what is the status of the deal? Choose exactly ONE word from this list:
INTERESTED (They want to know more or want a meeting)
NOT_INTERESTED (They said no, stop emailing)
OBJECTION (They have concerns but aren't a hard no)
CLOSED (They agreed to the price or gave access)

Also, write a 1-sentence instruction for the agency owner on what to do next to close this specific person.

Format your response exactly like this:
STATUS: [word]
NEXT_STEPS: [instruction]
"""
        analysis = analyzer.generate_content(analysis_prompt).text.strip()
        
        status = "INTERESTED"
        next_steps = "Call them immediately."
        
        for line in analysis.split('\n'):
            if line.startswith("STATUS:"):
                status = line.replace("STATUS:", "").strip()
            elif line.startswith("NEXT_STEPS:"):
                next_steps = line.replace("NEXT_STEPS:", "").strip()
                
        return expert_reply, status, next_steps
        
    except Exception as e:
        log.error("Gemini AI failed: %s", str(e))
        return ("Thank you for your reply. Let's schedule a quick 5-minute call to discuss how I can help.", "INTERESTED", "AI Failed, manual intervention required.")
