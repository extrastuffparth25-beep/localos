"""
scorer.py — Lead Qualification Scoring Engine for LOCALOS.

Scores each prospect based on signals that predict likelihood of becoming
a paying client:
  - Google rating (4+ stars = they care about quality)
  - Review count (established business with budget)
  - Website presence & quality
  - Whether they're running Google Ads (already spend on marketing)
  - Contact info availability
"""

from __future__ import annotations

import logging
import re

import requests
from bs4 import BeautifulSoup

from config import SCORE_WEIGHTS, SCORE_TIERS, REQUEST_TIMEOUT

log = logging.getLogger(__name__)

_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _check_website_seo(website_url: str) -> dict[str, bool]:
    """
    Quick SEO health check on a website.
    Returns signals indicating poor SEO (= opportunity for us).
    """
    signals = {
        "has_title": False,
        "has_meta_desc": False,
        "has_h1": False,
        "is_mobile_friendly": True,  # assume true unless proven otherwise
        "has_ssl": website_url.startswith("https"),
        "loads_fast": True,  # assume true for now
    }

    if not website_url or not website_url.startswith("http"):
        return signals

    try:
        resp = requests.get(
            website_url,
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return signals

        soup = BeautifulSoup(resp.text, "html.parser")

        # Check title tag
        if soup.title and soup.title.string and len(soup.title.string.strip()) > 5:
            signals["has_title"] = True

        # Check meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content", "").strip():
            signals["has_meta_desc"] = True

        # Check H1
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            signals["has_h1"] = True

        # Check viewport (mobile-friendly indicator)
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if not viewport:
            signals["is_mobile_friendly"] = False

        # Check page load time (slow = poor SEO)
        if resp.elapsed.total_seconds() > 5:
            signals["loads_fast"] = False

    except Exception as exc:
        log.debug("SEO check failed for %s: %s", website_url, exc)

    return signals


def score_lead(lead: dict[str, str]) -> tuple[int, str]:
    """
    Score a lead from 0-100 based on qualification signals.

    Returns (score, tier) where tier is 'A', 'B', or 'C'.
    """
    score = 0

    # ── Google Rating ──
    try:
        rating = float(lead.get("google_rating", 0))
        if rating >= 4.0:
            score += SCORE_WEIGHTS["rating_above_4"]
    except (ValueError, TypeError):
        pass

    # ── Review Count ──
    try:
        reviews = int(lead.get("review_count", 0))
        if reviews >= 50:
            score += SCORE_WEIGHTS["reviews_50_plus"]
        if reviews >= 100:
            score += SCORE_WEIGHTS["reviews_100_plus"]
    except (ValueError, TypeError):
        pass

    # ── Website Presence ──
    website = lead.get("website", "").strip()
    if website and website.startswith("http"):
        score += SCORE_WEIGHTS["has_website"]

        # Check website SEO quality
        seo_signals = _check_website_seo(website)
        poor_seo_count = sum([
            not seo_signals["has_title"],
            not seo_signals["has_meta_desc"],
            not seo_signals["has_h1"],
            not seo_signals["is_mobile_friendly"],
            not seo_signals["has_ssl"],
            not seo_signals["loads_fast"],
        ])
        if poor_seo_count >= 3:
            score += SCORE_WEIGHTS["poor_seo_signals"]
            log.debug("Poor SEO detected for %s (%d issues)", website, poor_seo_count)
    else:
        # No website = super hot lead (they need everything)
        score += SCORE_WEIGHTS["no_website"]

    # ── Running Ads ──
    is_running_ads = lead.get("running_ads", "").lower() in ("true", "yes", "1")
    if is_running_ads:
        score += SCORE_WEIGHTS["running_ads"]

    # ── Contact Info ──
    if lead.get("phone", "").strip():
        score += SCORE_WEIGHTS["has_phone"]

    if lead.get("email", "").strip() and "@" in lead.get("email", ""):
        score += SCORE_WEIGHTS["has_email"]

    # ── Determine Tier ──
    if score >= SCORE_TIERS["A"]:
        tier = "A"
    elif score >= SCORE_TIERS["B"]:
        tier = "B"
    else:
        tier = "C"

    return min(score, 100), tier


def score_leads_batch(leads: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Score a batch of leads, adding 'score' and 'tier' fields to each.
    """
    for i, lead in enumerate(leads):
        lead_score, tier = score_lead(lead)
        lead["score"] = str(lead_score)
        lead["tier"] = tier
        log.info(
            "[%d/%d] Scored: %s — %d pts (Tier %s)",
            i + 1, len(leads),
            lead.get("business_name", "Unknown"),
            lead_score, tier,
        )
    return leads
