"""
keyword_optimizer.py — Keyword strategy generator for LOCALOS.

Provides keyword recommendations for GBP categories, business
descriptions, and posts to maximize Local Pack visibility.
"""

from __future__ import annotations


# ──────────────────────────────────────────────
# Core Niche Keyword Mappings
# ──────────────────────────────────────────────
NICHE_KEYWORDS = {
    "Restaurant": {
        "primary_categories": ["Restaurant", "Family Restaurant", "Fine Dining Restaurant"],
        "core_keywords": ["best restaurant", "places to eat", "food near me", "dinner", "lunch"],
        "description_terms": ["fresh ingredients", "dine-in", "takeout", "reservations", "local favorite"],
    },
    "Dentist": {
        "primary_categories": ["Dentist", "Dental Clinic", "Cosmetic Dentist"],
        "core_keywords": ["dentist near me", "teeth cleaning", "dental implants", "family dentist", "emergency dentist"],
        "description_terms": ["accepting new patients", "gentle care", "dental insurance", "smile makeover"],
    },
    "Plumber": {
        "primary_categories": ["Plumber", "Drainage Service", "Emergency Plumber"],
        "core_keywords": ["plumber near me", "emergency plumber", "clogged drain", "water heater repair", "pipe leak"],
        "description_terms": ["24/7 service", "licensed and insured", "free estimates", "same-day service"],
    },
    "HVAC": {
        "primary_categories": ["HVAC Contractor", "Air Conditioning Repair Service", "Heating Contractor"],
        "core_keywords": ["ac repair", "furnace repair", "hvac company", "air conditioning service", "heater installation"],
        "description_terms": ["licensed technicians", "emergency repair", "energy efficient", "maintenance plan"],
    },
    "Salon": {
        "primary_categories": ["Beauty Salon", "Hair Salon", "Nail Salon"],
        "core_keywords": ["hair salon near me", "haircut", "balayage", "hair styling", "nail salon"],
        "description_terms": ["professional stylists", "walk-ins welcome", "luxury salon", "hair treatments"],
    },
    "Gym": {
        "primary_categories": ["Gym", "Fitness Center", "Personal Trainer"],
        "core_keywords": ["gym near me", "fitness center", "personal training", "group classes", "weight loss"],
        "description_terms": ["state-of-the-art equipment", "certified trainers", "open 24/7", "free trial"],
    },
    "Law Firm": {
        "primary_categories": ["Law Firm", "Attorney", "Personal Injury Attorney"],
        "core_keywords": ["lawyer near me", "attorney", "law firm", "legal consultation", "personal injury lawyer"],
        "description_terms": ["free consultation", "experienced attorneys", "legal representation", "no fee unless we win"],
    },
    "Auto Repair": {
        "primary_categories": ["Auto Repair Shop", "Mechanic", "Brake Shop"],
        "core_keywords": ["auto repair near me", "mechanic", "oil change", "brake repair", "car inspection"],
        "description_terms": ["certified mechanics", "honest pricing", "warranty", "free diagnostics"],
    },
}

DEFAULT_KEYWORDS = {
    "primary_categories": ["Service Establishment"],
    "core_keywords": ["local business", "services near me", "best in town"],
    "description_terms": ["professional service", "customer satisfaction", "local experts", "reliable"],
}


def generate_keyword_strategy(business_name: str, niche: str, city: str) -> dict[str, list[str]]:
    """
    Generate a complete keyword strategy for a client's GBP.

    Returns a dict with categories, primary_keywords, secondary_keywords,
    and a sample description.
    """
    data = NICHE_KEYWORDS.get(niche, DEFAULT_KEYWORDS)

    # Localize keywords
    primary_kws = [f"{kw} in {city}" for kw in data["core_keywords"][:3]]
    primary_kws.extend([f"{city} {kw}" for kw in data["core_keywords"][:2]])

    secondary_kws = [f"{kw} near me" for kw in data["core_keywords"]]

    # Build an optimized description
    desc_terms = ", ".join(data["description_terms"][:3])
    description = (
        f"Looking for the best {niche.lower()} in {city}? "
        f"{business_name} provides top-rated {data['core_keywords'][1]} and {data['core_keywords'][0]}. "
        f"We specialize in {desc_terms}. Call us today for the best {niche.lower()} service in the {city} area!"
    )

    return {
        "categories": data["primary_categories"],
        "primary_keywords": primary_kws,
        "secondary_keywords": secondary_kws,
        "optimized_description": description,
    }


def format_keyword_report(business_name: str, niche: str, city: str) -> str:
    """Format the keyword strategy into a readable report."""
    strategy = generate_keyword_strategy(business_name, niche, city)

    lines = []
    lines.append(f"{'═' * 60}")
    lines.append(f"🔑 GBP KEYWORD STRATEGY — {business_name}")
    lines.append(f"   Target Market: {city} | Industry: {niche}")
    lines.append(f"{'═' * 60}")

    lines.append("\n📁 RECOMMENDED CATEGORIES (Set these in GBP):")
    for cat in strategy["categories"]:
        lines.append(f"  • {cat}")

    lines.append("\n🎯 PRIMARY TARGET KEYWORDS (Track these):")
    for kw in strategy["primary_keywords"]:
        lines.append(f"  • {kw.title()}")

    lines.append("\n📝 OPTIMIZED BUSINESS DESCRIPTION (Copy-paste to GBP):")
    lines.append("-" * 50)
    lines.append(strategy["optimized_description"])
    lines.append("-" * 50)

    lines.append(f"\n{'═' * 60}\n")
    return "\n".join(lines)
