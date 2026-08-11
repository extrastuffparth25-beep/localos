"""
self_optimizer.py — AGI Autonomy Engine for LOCALOS.
Analyzes CRM data, fires underperforming markets, and uses AI to pivot into new profitable niches and cities.
"""

import json
import csv
import logging
import os
from pathlib import Path
from datetime import datetime, date

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config import NICHES, ALL_CITIES, LEADS_CSV

log = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

TARGETS_FILE = Path(__file__).parent / "targets.json"
OPTIMIZER_LOG = Path(__file__).parent / "optimizer_log.json"

if GEMINI_API_KEY and genai:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
else:
    model = None

def get_current_targets() -> dict:
    """Load current targets, or default to config.py if no history."""
    if TARGETS_FILE.exists():
        with open(TARGETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {
        "niches": NICHES,
        "cities": ALL_CITIES,
        "banned_markets": [] # List of "Niche in City"
    }

def analyze_crm(leads: list[dict]) -> dict:
    """Calculates performance for every market."""
    markets = {} # key: "Niche in City", value: {contacted, replied, won}
    
    for lead in leads:
        niche = lead.get("niche")
        city = lead.get("city")
        status = lead.get("status", "New")
        
        if not niche or not city:
            continue
            
        market_key = f"{niche} in {city}"
        if market_key not in markets:
            markets[market_key] = {"niche": niche, "city": city, "contacted": 0, "replied": 0, "won": 0}
            
        if status != "New":
            markets[market_key]["contacted"] += 1
            
        if status in ["Replied", "Won", "Lost"]:
            markets[market_key]["replied"] += 1
            
        if status == "Won":
            markets[market_key]["won"] += 1
            
    return markets

def generate_new_markets(winners: list[dict]) -> dict:
    """Ask Gemini to brainstorm new highly profitable targets based on current winners."""
    if not model or not winners:
        return {"niches": [], "cities": []}
        
    winners_str = "\n".join([f"{w['niche']} in {w['city']} (Reply Rate: {w['reply_rate']:.1%})" for w in winners])
    
    prompt = f"""
You are an elite business strategist for a highly profitable Local SEO agency.
Our current winning markets (high reply rates) are:
{winners_str}

Based on these winners, suggest 2 brand new, highly profitable niches and 2 brand new wealthy 1st-world cities (US/UK/CA/AU only) for us to scale into. 
The niches must be service-based businesses that make at least $1,000 per customer (e.g. Roofers, Cosmetic Dentists).

Output strictly in JSON format matching this schema:
{{
    "niches": [
        {{
            "name": "Niche Name",
            "keywords": ["keyword 1", "keyword 2"],
            "queries": ["best {{niche}} in {{city}}", "{{city}} {{niche}} near me"]
        }}
    ],
    "cities": ["City 1", "City 2"]
}}
"""
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        log.error("Optimizer AI failed: %s", str(e))
        return {"niches": [], "cities": []}

def run_self_optimizer(leads: list[dict]):
    """Execute the learning loop."""
    log.info("🤖 Waking up Self-Optimizing Strategy Engine...")
    
    targets = get_current_targets()
    banned_markets = set(targets.get("banned_markets", []))
    
    market_stats = analyze_crm(leads)
    
    winners = []
    fired = 0
    
    for market_key, stats in market_stats.items():
        if stats["contacted"] == 0:
            continue
            
        reply_rate = stats["replied"] / stats["contacted"]
        stats["reply_rate"] = reply_rate
        
        # Fire bad markets (More than 150 contacted, 0 replies)
        if stats["contacted"] >= 150 and stats["replied"] == 0:
            log.warning("🔥 FIRING MARKET: %s (0%% reply rate after %d emails). Banning permanently.", market_key, stats["contacted"])
            banned_markets.add(market_key)
            fired += 1
            
        # Identify winners (More than 4% reply rate after statistical significance)
        if stats["contacted"] >= 25 and reply_rate >= 0.04:
            winners.append(stats)
            
    # Brainstorm new markets if we have winners
    if winners:
        log.info("🧠 Analyzing %d winning markets. Brainstorming expansion...", len(winners))
        new_ideas = generate_new_markets(winners)
        
        if new_ideas.get("niches"):
            for n in new_ideas["niches"]:
                if n["name"] not in [t["name"] for t in targets["niches"]]:
                    log.info("📈 EXPANDING: AI discovered new profitable niche -> %s", n["name"])
                    targets["niches"].append(n)
                    
        if new_ideas.get("cities"):
            for c in new_ideas["cities"]:
                if c not in targets["cities"]:
                    log.info("📈 EXPANDING: AI discovered new profitable city -> %s", c)
                    targets["cities"].append(c)
                    
    # Save targets
    targets["banned_markets"] = list(banned_markets)
    with open(TARGETS_FILE, "w", encoding="utf-8") as f:
        json.dump(targets, f, indent=2)
        
    # Log the optimization run
    run_log = {
        "date": str(date.today()),
        "total_markets_analyzed": len(market_stats),
        "markets_fired": fired,
        "new_niches_added": len(new_ideas.get("niches", [])) if winners else 0,
        "new_cities_added": len(new_ideas.get("cities", [])) if winners else 0,
        "winners": winners
    }
    
    try:
        if OPTIMIZER_LOG.exists():
            with open(OPTIMIZER_LOG, "r") as f:
                logs = json.load(f)
        else:
            logs = []
    except:
        logs = []
        
    logs.append(run_log)
    with open(OPTIMIZER_LOG, "w") as f:
        json.dump(logs, f, indent=2)
        
    log.info("✅ Optimization Complete. Strategy updated.")

if __name__ == "__main__":
    # Test block
    if Path(LEADS_CSV).exists():
        with open(LEADS_CSV, "r", encoding="utf-8") as f:
            leads = list(csv.DictReader(f))
        run_self_optimizer(leads)
