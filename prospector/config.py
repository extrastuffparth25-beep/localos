"""
config.py — Central configuration for the LOCALOS Lead Prospector.

All tuneable parameters for the Google Maps lead finding system.
"""

import os

# ──────────────────────────────────────────────
# Target Markets (Global)
# ──────────────────────────────────────────────
TARGET_CITIES: dict[str, list[str]] = {
    "USA": [
        "Dallas TX", "Miami FL", "Los Angeles CA", "New York NY",
        "Chicago IL", "Houston TX", "Denver CO", "Austin TX",
        "San Francisco CA", "Phoenix AZ", "Atlanta GA", "Seattle WA",
        "Portland OR", "Nashville TN", "Charlotte NC", "Tampa FL",
        "San Diego CA", "Las Vegas NV", "Boston MA", "Minneapolis MN",
    ],
    "UK": [
        "London", "Manchester", "Birmingham", "Leeds", "Glasgow",
        "Liverpool", "Bristol", "Edinburgh", "Sheffield", "Cardiff",
    ],
    "Canada": [
        "Toronto", "Vancouver", "Calgary", "Montreal", "Ottawa",
        "Edmonton", "Winnipeg", "Halifax", "Victoria", "Hamilton",
    ],
    "Australia": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Gold Coast", "Canberra", "Hobart", "Darwin", "Newcastle",
    ],
}

# Flatten all cities for easy iteration
ALL_CITIES: list[str] = []
for country, cities in TARGET_CITIES.items():
    for city in cities:
        ALL_CITIES.append(f"{city}")

# ──────────────────────────────────────────────
# Target Niches
# ──────────────────────────────────────────────
NICHES: list[dict[str, str]] = [
    {
        "name": "Restaurant",
        "keywords": ["restaurant", "cafe", "bistro", "eatery", "diner", "pizzeria", "sushi"],
        "queries": [
            "{niche} near {city}",
            "best {niche} {city}",
            "{niche} in {city}",
        ],
    },
    {
        "name": "Dentist",
        "keywords": ["dentist", "dental", "orthodontist", "dental clinic", "dental office"],
        "queries": [
            "dentist near {city}",
            "best dentist {city}",
            "dental clinic {city}",
        ],
    },
    {
        "name": "Plumber",
        "keywords": ["plumber", "plumbing", "drain", "pipe", "water heater"],
        "queries": [
            "plumber near {city}",
            "plumbing services {city}",
            "emergency plumber {city}",
        ],
    },
    {
        "name": "HVAC",
        "keywords": ["hvac", "air conditioning", "heating", "furnace", "ac repair"],
        "queries": [
            "hvac repair {city}",
            "air conditioning service {city}",
            "ac repair near {city}",
        ],
    },
    {
        "name": "Electrician",
        "keywords": ["electrician", "electrical", "wiring", "electric"],
        "queries": [
            "electrician near {city}",
            "electrical contractor {city}",
            "emergency electrician {city}",
        ],
    },
    {
        "name": "Real Estate",
        "keywords": ["realtor", "real estate agent", "real estate", "property", "realty"],
        "queries": [
            "real estate agent {city}",
            "realtor near {city}",
            "best realtor {city}",
        ],
    },
    {
        "name": "Gym",
        "keywords": ["gym", "fitness", "CrossFit", "personal trainer", "yoga studio"],
        "queries": [
            "gym near {city}",
            "fitness center {city}",
            "best gym {city}",
        ],
    },
    {
        "name": "Salon",
        "keywords": ["salon", "barber", "spa", "hair salon", "nail salon", "beauty"],
        "queries": [
            "hair salon {city}",
            "best salon near {city}",
            "spa {city}",
        ],
    },
    {
        "name": "Law Firm",
        "keywords": ["lawyer", "attorney", "law firm", "legal", "law office"],
        "queries": [
            "lawyer near {city}",
            "best law firm {city}",
            "attorney {city}",
        ],
    },
    {
        "name": "Auto Repair",
        "keywords": ["auto repair", "mechanic", "car repair", "auto shop", "garage"],
        "queries": [
            "auto repair near {city}",
            "mechanic {city}",
            "car repair shop {city}",
        ],
    },
]

# ──────────────────────────────────────────────
# Prospecting Behaviour
# ──────────────────────────────────────────────
DAILY_TARGET: int = 15              # leads WITH EMAILS to collect per run
MAX_RETRY_CYCLES: int = 3           # full city-shuffle retries
MAX_PAGES_PER_LEAD: int = 2         # deep crawl page limit (faster)
REQUEST_DELAY_RANGE: tuple[int, int] = (1, 3)  # seconds between requests (exponential backoff padding)
REQUEST_TIMEOUT: int = 15           # HTTP timeout in seconds
MAX_SEARCH_RESULTS: int = 25        # results to fetch per query

# ──────────────────────────────────────────────
# Lead Scoring Thresholds
# ──────────────────────────────────────────────
SCORE_WEIGHTS = {
    "rating_above_4": 20,           # Has 4+ star rating (they care about quality)
    "reviews_50_plus": 15,          # 50+ reviews = established business
    "reviews_100_plus": 10,         # Bonus for 100+ reviews
    "has_website": 10,              # Has a website (but we'll check its SEO)
    "no_website": 25,               # NO website = super hot lead
    "running_ads": 20,              # Already spending on marketing
    "poor_seo_signals": 15,         # Website has poor SEO (missing meta, slow)
    "has_phone": 5,                 # Contact info available
    "has_email": 10,                # Direct email found
}

SCORE_TIERS = {
    "A": 60,   # HOT — prioritize these
    "B": 40,   # WARM — good prospects
    "C": 20,   # COLD — worth a try
}

# ──────────────────────────────────────────────
# Data Persistence
# ──────────────────────────────────────────────
LEADS_CSV: str = "prospects.csv"

CSV_FIELDNAMES: list[str] = [
    "business_name",
    "niche",
    "city",
    "country",
    "phone",
    "email",
    "website",
    "google_rating",
    "review_count",
    "running_ads",
    "score",
    "tier",
    "date_scraped",
    "status",
    "sequence_step",
    "last_contact_date",
    "conversation_history",
    "top_competitor"
]

# ──────────────────────────────────────────────
# Email Configuration
# ──────────────────────────────────────────────
GMAIL_SMTP_HOST: str = "smtp.gmail.com"
GMAIL_SMTP_PORT: int = 587
RECIPIENT_EMAIL: str = os.environ.get("GMAIL_USER", "")
NOTIFICATION_RECIPIENT: str = os.environ.get("GMAIL_USER", "")

GMAIL_USER: str = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD: str = os.environ.get("GMAIL_APP_PASSWORD", "")

# Outreach email account (separate from digest emails)
OUTREACH_GMAIL_USER: str = os.environ.get("OUTREACH_GMAIL_USER", "")
OUTREACH_GMAIL_APP_PASSWORD: str = os.environ.get("OUTREACH_GMAIL_APP_PASSWORD", "")
OUTREACH_IMAP_HOST: str = "imap.gmail.com"
OUTREACH_IMAP_PORT: int = 993

NOTIFICATION_RECIPIENT: str = "extrastuff.parth25@gmail.com"

# ──────────────────────────────────────────────
# Domains to skip when scraping
# ──────────────────────────────────────────────
SKIP_DOMAINS: set[str] = {
    # Search engines
    "google.com", "google.co.uk", "google.com.au", "google.co.in",
    "bing.com", "duckduckgo.com", "yahoo.com", "yandex.com",
    # Social media
    "youtube.com", "facebook.com", "twitter.com", "x.com",
    "linkedin.com", "reddit.com", "pinterest.com", "tiktok.com",
    "instagram.com",
    # Directories & aggregators
    "yelp.com", "yellowpages.com", "bbb.org", "manta.com",
    "thumbtack.com", "bark.com", "angi.com", "homeadvisor.com",
    "tripadvisor.com", "trustpilot.com", "houzz.com",
    "porch.com", "nextdoor.com", "alignable.com",
    "healthgrades.com", "zocdoc.com", "vitals.com",
    # Job boards
    "indeed.com", "glassdoor.com", "craigslist.org", "upwork.com",
    "fiverr.com", "freelancer.com",
    # Reference
    "wikipedia.org", "britannica.com",
    # Shopping
    "amazon.com", "ebay.com",
    # News
    "nytimes.com", "bbc.com", "cnn.com", "forbes.com",
    # Tech
    "github.com", "medium.com", "quora.com", "stackoverflow.com",
    # Map / listing aggregators
    "mapquest.com", "foursquare.com",
}

EMAIL_BLACKLIST_DOMAINS: set[str] = {
    "example.com", "example.org", "test.com",
    "sentry.io", "wixpress.com", "squarespace.com",
    "wordpress.com", "godaddy.com", "googleapis.com",
    "googleusercontent.com", "fbcdn.net", "cdninstagram.com",
    "schema.org", "w3.org", "apple.com", "microsoft.com",
    "github.com", "twitter.com", "facebook.com",
}

EMAIL_BLACKLIST_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
}
