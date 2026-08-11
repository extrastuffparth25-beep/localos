"""
post_generator.py — AI GBP Post Generator for LOCALOS.

Generates weekly Google Business Profile posts for each client.
Posts are niche-specific, keyword-optimized, and ready to copy-paste
into the GBP dashboard.
"""

from __future__ import annotations

import random
from datetime import date, timedelta


# ──────────────────────────────────────────────
# Post Templates by Niche
# ──────────────────────────────────────────────
POST_TEMPLATES: dict[str, list[str]] = {
    "Restaurant": [
        "🍽️ {greeting}! This week at {business}, we're serving up something special. Come in and try our {seasonal} menu — made with fresh, locally-sourced ingredients. Reserve your table today! #{city}Eats #{niche}",
        "✨ Nothing beats a great meal with great company. At {business}, every dish is crafted with care. Stop by this {day} and see why we're one of {city}'s favorite spots! #{city}Food #BestRestaurant{city}",
        "📸 Have you tried our {popular_item} yet? Our guests can't stop talking about it! Come visit {business} in {city} and taste the difference. #FoodLover #{city}Dining",
        "🎉 Weekend plans? Let us take care of dinner! At {business}, we combine amazing flavors with a cozy atmosphere. Walk-ins welcome, reservations recommended. #{niche}In{city}",
    ],
    "Dentist": [
        "😁 A healthy smile starts with regular check-ups! At {business}, we make dental care comfortable and stress-free. Book your appointment today. #{city}Dentist #DentalCare",
        "✨ Did you know? Regular cleanings can prevent 80% of dental problems. At {business} in {city}, we're here to keep your smile bright and healthy! #OralHealth #{niche}{city}",
        "🦷 Looking for a family dentist in {city}? {business} offers gentle care for patients of all ages — from kids' first visits to cosmetic treatments. Call us today! #FamilyDentist",
        "💡 {seasonal} is the perfect time to use your dental benefits before they expire! Schedule your visit at {business} — we accept most insurance plans. #{city}DentalCare",
    ],
    "Plumber": [
        "🔧 Leaky faucet? Clogged drain? {business} in {city} provides fast, reliable plumbing service — often same-day! Call us for a free estimate. #{city}Plumber #PlumbingService",
        "🏠 Protect your home from water damage! {business} offers professional pipe inspections and repairs. Don't wait until it's an emergency. #{niche}{city} #HomeMaintenance",
        "⚡ {seasonal} plumbing tip: {seasonal_tip}. Need help? {business} is {city}'s trusted plumbing expert! 24/7 emergency service available. #PlumbingTips #{city}",
        "⭐ Thank you {city} for trusting {business} with your plumbing needs! We're proud to serve our community with honest, affordable service. #{city}Plumbing #LocalBusiness",
    ],
    "HVAC": [
        "❄️ Is your AC ready for {season}? {business} in {city} offers tune-ups, repairs, and installations at competitive prices. Stay comfortable all {season}! #{city}HVAC #ACRepair",
        "🌡️ Don't let a broken AC ruin your {day}! {business} provides same-day HVAC service in {city}. Call now for fast, professional help. #{niche}{city} #HVACService",
        "💡 Pro tip: Changing your air filter every 1-3 months can reduce energy bills by up to 15%! Need HVAC help? {business} is here for you. #EnergyEfficiency #{city}",
        "🏆 Why choose {business}? Licensed technicians, upfront pricing, and a satisfaction guarantee. {city}'s most trusted HVAC company! #{city}Heating #AirConditioning",
    ],
    "Salon": [
        "💇 New season, new look! Book your appointment at {business} in {city} and let our stylists transform your hair. Walk-ins welcome! #{city}Salon #HairStylist",
        "✨ Treat yourself this {day}! {business} offers cuts, color, styling, and spa services in the heart of {city}. You deserve it! #SalonLife #{niche}{city}",
        "🌟 Our clients love their results — and you will too! Visit {business} for a premium salon experience at affordable prices. #{city}Hair #BeautySalon",
        "💅 Looking for the best salon in {city}? {business} combines expert stylists with a relaxing atmosphere. Book online or call us today! #HairGoals #{city}Beauty",
    ],
    "Gym": [
        "💪 Your fitness journey starts here! {business} in {city} offers state-of-the-art equipment, group classes, and personal training. First week FREE! #{city}Gym #FitnessGoals",
        "🏋️ No excuses this {day}! Come crush your workout at {business}. Whether you're a beginner or a pro, we've got you covered. #{niche}{city} #WorkOut",
        "🔥 New classes alert! Check out our updated schedule at {business}. HIIT, Yoga, Spin, and more — all included in your membership! #{city}Fitness #GymLife",
        "⭐ Results you can see! Our members are achieving amazing transformations. Join {business} today and start your journey. #{city}Gym #FitnessMotivation",
    ],
    "Law Firm": [
        "⚖️ Legal matters require expert guidance. At {business}, our experienced attorneys provide personalized legal solutions for {city} residents. Free consultation available. #{city}Lawyer #LegalAdvice",
        "📋 Don't face legal challenges alone. {business} in {city} is here to protect your rights and fight for the best outcome. Call us today. #{niche}{city} #Attorney",
        "💼 Need a trusted attorney in {city}? {business} has been serving our community with integrity and results. Schedule your free case review. #{city}LawFirm",
        "🏛️ {business} — {city}'s trusted legal partner. We specialize in providing clear, honest legal advice when you need it most. #LegalHelp #{city}Attorney",
    ],
    "Auto Repair": [
        "🚗 Is your car making that noise again? {business} in {city} provides honest, affordable auto repair. Free diagnostics with any service! #{city}AutoRepair #CarMaintenance",
        "🔧 Trust {business} for all your car needs — oil changes, brake repair, engine diagnostics, and more. {city}'s most reliable mechanic! #{niche}{city} #AutoShop",
        "💡 {seasonal} car care tip: {seasonal_tip}. Need service? {business} is {city}'s go-to auto repair shop! #CarCareTips #{city}Mechanic",
        "⭐ 5-star service, transparent pricing. That's the {business} promise. Bring your car to us and see why {city} trusts us! #{city}AutoRepair #TrustedMechanic",
    ],
}

# Default templates for niches not explicitly defined
DEFAULT_TEMPLATES = [
    "📢 {business} in {city} is here to serve you! We pride ourselves on quality, reliability, and excellent customer service. Contact us today! #{city}{niche} #LocalBusiness",
    "⭐ Thank you {city} for your continued trust in {business}! We're committed to providing the best {niche} services in the area. #{niche}{city}",
    "💡 Looking for a trusted {niche} in {city}? {business} has you covered! Professional service, competitive prices, and results you can count on. #{city}Business",
    "🌟 This {day} is the perfect time to take care of {niche_needs}! {business} in {city} makes it easy. Call or visit us today! #{niche}{city} #QualityService",
]


# ──────────────────────────────────────────────
# Seasonal & Dynamic Content
# ──────────────────────────────────────────────
SEASONAL_MAP = {
    1: ("Winter", "Start the new year right", "Check your pipes for freeze protection before temperatures drop"),
    2: ("Winter", "Love is in the air", "Get your heating system inspected before the last cold snap"),
    3: ("Spring", "Spring is here", "Check for winter damage and schedule spring maintenance"),
    4: ("Spring", "April showers", "Inspect outdoor drains and gutters to prevent flooding"),
    5: ("Late Spring", "Summer's almost here", "Schedule your AC tune-up before the heat hits"),
    6: ("Summer", "Beat the heat", "Have your AC filters changed to keep cool efficiently"),
    7: ("Summer", "Hot summer days", "Stay hydrated and keep your systems running smoothly"),
    8: ("Late Summer", "Back-to-school season", "Get ready for fall with a maintenance check"),
    9: ("Fall", "Autumn vibes", "Prepare for cooler weather with a heating system check"),
    10: ("Fall", "Cozy season", "Schedule furnace maintenance before the first freeze"),
    11: ("Holiday season", "Holiday preparations", "Get your home holiday-ready with a quick maintenance check"),
    12: ("Holiday season", "Year-end celebrations", "Book your year-end appointments before slots fill up"),
}

POPULAR_ITEMS = {
    "Restaurant": ["signature pasta", "chef's special", "weekend brunch", "craft cocktails", "dessert platter"],
    "Dentist": ["teeth whitening", "Invisalign", "dental implants", "cosmetic veneers"],
    "Salon": ["balayage highlights", "keratin treatment", "fresh cut", "color refresh"],
    "Gym": ["personal training session", "group fitness class", "nutrition coaching"],
}

NICHE_NEEDS = {
    "Plumber": "your plumbing",
    "HVAC": "your heating and cooling",
    "Electrician": "your electrical systems",
    "Dentist": "your dental health",
    "Salon": "your hair and beauty",
    "Restaurant": "dinner plans",
    "Gym": "your fitness goals",
    "Law Firm": "your legal needs",
    "Auto Repair": "your car maintenance",
    "Real Estate": "your home search",
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_weekly_posts(
    business_name: str,
    niche: str,
    city: str,
    num_posts: int = 4,
) -> list[dict[str, str]]:
    """
    Generate a week's worth of GBP posts for a client.

    Returns a list of dicts with: post_date, content, niche, city.
    """
    month = date.today().month
    season, seasonal, seasonal_tip = SEASONAL_MAP.get(month, ("", "", ""))
    day = random.choice(DAYS)
    popular = random.choice(POPULAR_ITEMS.get(niche, ["our services"]))
    niche_need = NICHE_NEEDS.get(niche, "your needs")

    # Get niche-specific templates or fall back to defaults
    templates = POST_TEMPLATES.get(niche, DEFAULT_TEMPLATES)

    # Pick random templates without repeating
    selected = random.sample(templates, min(num_posts, len(templates)))
    if len(selected) < num_posts:
        # Fill remaining with defaults
        remaining = num_posts - len(selected)
        selected.extend(random.sample(DEFAULT_TEMPLATES, min(remaining, len(DEFAULT_TEMPLATES))))

    posts = []
    base_date = date.today()

    for i, template in enumerate(selected):
        post_date = base_date + timedelta(days=i * 2)  # Every 2 days

        content = template.format(
            business=business_name,
            city=city.replace(" ", ""),
            niche=niche.replace(" ", ""),
            seasonal=seasonal,
            season=season,
            day=day,
            popular_item=popular,
            seasonal_tip=seasonal_tip,
            niche_needs=niche_need,
            greeting="Happy " + day,
        )

        posts.append({
            "post_date": post_date.strftime("%Y-%m-%d"),
            "day_name": post_date.strftime("%A"),
            "content": content,
            "niche": niche,
            "city": city,
            "character_count": len(content),
        })

    return posts


def format_weekly_plan(
    business_name: str,
    niche: str,
    city: str,
    num_posts: int = 4,
) -> str:
    """
    Generate and format a weekly posting plan for copy-paste.
    """
    posts = generate_weekly_posts(business_name, niche, city, num_posts)

    lines = []
    lines.append(f"{'═' * 60}")
    lines.append(f"📝 WEEKLY GBP POST PLAN — {business_name}")
    lines.append(f"   Niche: {niche} | City: {city}")
    lines.append(f"   Generated: {date.today().strftime('%B %d, %Y')}")
    lines.append(f"{'═' * 60}")

    for i, post in enumerate(posts, 1):
        lines.append(f"\n{'─' * 50}")
        lines.append(f"📅 POST {i} — {post['day_name']}, {post['post_date']}")
        lines.append(f"Characters: {post['character_count']}")
        lines.append(f"{'─' * 50}")
        lines.append(f"\n{post['content']}")

    lines.append(f"\n{'═' * 60}")
    lines.append(f"💡 TIP: Post at 10-11 AM local time for best engagement")
    lines.append(f"{'═' * 60}\n")

    return "\n".join(lines)
