"""
keyword_optimizer.py — AI-Powered Keyword strategy generator for LOCALOS.
Uses Gemini to generate god-level, bespoke Local SEO strategies.
"""

import logging
import google.generativeai as genai
from config import GEMINI_API_KEY

log = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def generate_keyword_strategy(business_name: str, niche: str, city: str) -> str:
    """Uses AI to generate an elite keyword strategy."""
    if not model:
        return "ERROR: Gemini API Key missing for SEO Fulfillment."
        
    prompt = f"""
Act as an elite, world-class Local SEO expert. Your client is paying a premium rate ($500/mo) for the highest quality Local SEO strategy available.
Generate a highly-optimized Google Business Profile category and keyword strategy for {business_name}, a {niche} in {city}.

Output exactly in this format with no fluff. Ensure the keywords are deeply researched, high-intent, and mathematically proven to drive local traffic. Do not output anything generic:

PRIMARY CATEGORY:
[The absolute best GMB category]

SECONDARY CATEGORIES:
- [Category 2]
- [Category 3]

TOP 10 LOCAL SEARCH KEYWORDS (To sprinkle in profile and posts):
1. [Keyword] (High intent)
...
10. [Keyword]

OPTIMIZED BUSINESS DESCRIPTION (Copy-paste ready):
[A highly engaging, keyword-rich 750-character business description]
"""
    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.3})
        return response.text.strip()
    except Exception as e:
        log.error("Failed to generate keyword strategy: %s", str(e))
        return "ERROR: AI Generation Failed."
