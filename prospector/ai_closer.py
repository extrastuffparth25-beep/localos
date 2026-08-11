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
Your goal is to CLOSE THE DEAL with a local business owner who just replied to your cold email.

YOUR SERVICE: You optimize Google Business Profiles (Google Maps) to rank them in the top 3.
YOUR PRICE: $500/month flat. No contracts.
YOUR OFFER: A free audit and a guarantee that if they don't get more calls in 30 days, they don't pay.

YOUR RULES OF NEGOTIATION:
1. Act like a highly paid, busy expert. Be extremely concise. No long essays. 
2. Match their tone. If they are brief, you be brief.
3. If they ask for pricing, TELL THEM IMMEDIATELY. "It's $500 flat. No setup fees." Do not hide it.
4. If they say they have someone doing it, say: "If they were doing a good job, you wouldn't be ranked #12. Let me show you what they missed."
5. If they ask for next steps, push for a 10-minute phone call OR ask them to add you as a Manager to their Google Business Profile to start the free trial.
6. NEVER sound like a bot. Sound like a human typing on an iPhone (use contractions, short sentences).
7. ONLY output the exact email response you want to send back. No subject line, just the body text.

The conversation history and their latest reply will be provided to you.
"""

def generate_expert_reply(business_name: str, niche: str, city: str, thread_history: str, latest_reply: str) -> tuple[str, str, str]:
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
        response = model.generate_content(prompt, generation_config={"temperature": 0.4})
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
