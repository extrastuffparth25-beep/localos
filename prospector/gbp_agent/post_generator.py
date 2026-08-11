"""
post_generator.py — AI-Powered Post Generator for LOCALOS.
Uses Gemini to write hyper-engaging, niche-specific Google Business Posts.
"""

import logging
from datetime import date
import google.generativeai as genai
from config import GEMINI_API_KEY

log = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def generate_monthly_posts(business_name: str, niche: str, client_requests: str = "") -> str:
    """Uses AI to generate a month's worth of GBP posts."""
    if not model:
        return "ERROR: Gemini API Key missing for SEO Fulfillment."
        
    prompt = f"""
Act as an elite, world-class Local SEO copywriter. Your client is paying a premium rate ($500/mo) for the highest quality Google Business Profile posts.
Generate a 1-month posting strategy (4 weekly posts) for {business_name}, a {niche}.
Client notes/requests: {client_requests}

Output exactly in this format with no fluff. Ensure the posts are highly engaging, keyword-rich, use emojis, and end with a strong Call-To-Action (CTA). 

--- WEEK 1 POST ---
[Engaging post content, 50-70 words]

--- WEEK 2 POST ---
[Engaging post content, 50-70 words]

--- WEEK 3 POST ---
[Engaging post content, 50-70 words]

--- WEEK 4 POST ---
[Engaging post content, 50-70 words]
"""
    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.6})
        return response.text.strip()
    except Exception as e:
        log.error("Failed to generate posts: %s", str(e))
        return "ERROR: AI Generation Failed."
