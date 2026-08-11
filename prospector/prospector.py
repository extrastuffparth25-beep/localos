"""
prospector.py — Google Maps Lead Prospector for LOCALOS.

Finds local businesses that are buried on Google Maps (not in top 3)
and extracts their contact info for outreach.

Uses the same proven multi-source search approach from lead-scraper:
  DuckDuckGo → Google → Bing (fallback chain)

Enhanced with business-specific data extraction:
  - Google rating & review count
  - Phone, email, website
  - Whether they're running Google Ads
"""

from __future__ import annotations

import logging
import os
import random
import re
import time
from collections import defaultdict
from typing import Any
from urllib.parse import urljoin, urlparse, quote
from datetime import date

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from config import (
    ALL_CITIES,
    CSV_FIELDNAMES,
    DAILY_TARGET,
    EMAIL_BLACKLIST_DOMAINS,
    EMAIL_BLACKLIST_EXTENSIONS,
    MAX_PAGES_PER_LEAD,
    MAX_RETRY_CYCLES,
    MAX_SEARCH_RESULTS,
    NICHES,
    REQUEST_DELAY_RANGE,
    REQUEST_TIMEOUT,
    SKIP_DOMAINS,
    TARGET_CITIES,
)
from scorer import score_lead

# Stealth Engine: Rotating User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Regex Patterns
# ──────────────────────────────────────────────
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-.]?)?"
    r"\(?\d{2,4}\)?[\s\-.]?"
    r"\d{3,4}[\s\-.]?"
    r"\d{3,4}",
)


# ──────────────────────────────────────────────
# HTTP Helpers
# ──────────────────────────────────────────────
def _fetch_html(url: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """Fetch HTML content with a timeout, generic headers, and exponential backoff."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    retries = 3
    backoff = 2
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code in [403, 429]:
                log.warning("Rate limited (HTTP %s) on %s. Backing off for %ds...", resp.status_code, url, backoff)
                time.sleep(backoff)
                backoff *= 2
            else:
                break
        except requests.exceptions.RequestException:
            pass
    return ""


def _polite_delay() -> None:
    """Sleep for a random interval to stay under rate limits."""
    time.sleep(random.uniform(*REQUEST_DELAY_RANGE))


def _domain_of(url: str) -> str:
    """Return the registerable domain portion of a URL."""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host


# ──────────────────────────────────────────────
# Search Sources (reused pattern from lead-scraper)
# ──────────────────────────────────────────────
def search_duckduckgo(query: str, max_results: int = MAX_SEARCH_RESULTS) -> list[dict[str, str]]:
    """Search DuckDuckGo using duckduckgo_search library with backoff."""
    results = []
    retries = 3
    backoff = 2
    
    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                # Need to use 'text' generator and limit the results
                raw_results = list(ddgs.text(query, max_results=max_results))
                for r in raw_results:
                    results.append({
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", "")
                    })
                return results
        except Exception as e:
            if "RateLimit" in str(e) or "429" in str(e):
                log.warning("DDG Rate limit hit. Backing off %ds...", backoff)
                time.sleep(backoff)
                backoff *= 2
            else:
                log.debug("DDG search failed: %s", str(e))
                break
    return results


def search_google(query: str) -> list[dict[str, str]]:
    """Return results from Google."""
    try:
        from googlesearch import search as gsearch
        results = []
        for url in gsearch(query, num_results=MAX_SEARCH_RESULTS, sleep_interval=3):
            results.append({"title": "", "href": url, "body": ""})
        log.info("Google returned %d results for: %s", len(results), query)
        return results
    except Exception as exc:
        log.warning("Google search failed: %s", exc)
        return []


def search_bing(query: str) -> list[dict[str, str]]:
    """Scrape Bing search results page directly."""
    try:
        url = f"https://www.bing.com/search?q={quote(query)}&count={MAX_SEARCH_RESULTS}"
        html = _fetch_html(url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for li in soup.select("li.b_algo"):
            link_tag = li.select_one("h2 a")
            snippet_tag = li.select_one(".b_caption p")
            if link_tag and link_tag.get("href"):
                results.append({
                    "title": link_tag.get_text(strip=True),
                    "href": link_tag["href"],
                    "body": snippet_tag.get_text(strip=True) if snippet_tag else "",
                })
        log.info("Bing returned %d results for: %s", len(results), query)
        return results
    except Exception as exc:
        log.warning("Bing search failed: %s", exc)
        return []


# ──────────────────────────────────────────────
# Contact Extraction
# ──────────────────────────────────────────────
def _extract_emails(text: str) -> set[str]:
    """Pull all plausible email addresses from raw text."""
    candidates = set(_EMAIL_RE.findall(text.lower()))
    cleaned = set()
    for email in candidates:
        domain = email.split("@", 1)[1]
        if domain in EMAIL_BLACKLIST_DOMAINS:
            continue
        if any(email.endswith(ext) for ext in EMAIL_BLACKLIST_EXTENSIONS):
            continue
        if re.search(r"\d+x\.\w+$", email):
            continue
        cleaned.add(email)
    return cleaned


def _extract_phones(text: str) -> set[str]:
    """Pull phone-number-like strings."""
    raw = set(_PHONE_RE.findall(text))
    cleaned = set()
    for phone in raw:
        if re.search(r"\.\d{5,}", phone):
            continue
        digits_only = re.sub(r"\D", "", phone)
        if 7 <= len(digits_only) <= 15:
            cleaned.add(phone.strip())
    return cleaned


def _extract_business_name(url: str, soup: BeautifulSoup) -> str:
    """Best-effort business name from OG tags, <title>, or domain."""
    og = soup.find("meta", property="og:site_name")
    if og and og.get("content", "").strip():
        return og["content"].strip()[:120]

    if soup.title and soup.title.string:
        raw = soup.title.string.strip()
        for sep in [" | ", " - ", " — ", " – ", " :: "]:
            if sep in raw:
                raw = raw.split(sep)[0].strip()
        if raw:
            return raw[:120]

    domain = _domain_of(url).split(".")[0]
    return domain.replace("-", " ").replace("_", " ").title()[:120]


def _extract_rating_from_page(text: str) -> tuple[str, str]:
    """
    Try to extract Google rating and review count from page text.
    Returns (rating, review_count) as strings.
    """
    rating = ""
    review_count = ""

    # Look for patterns like "4.5 stars" or "4.5/5"
    rating_match = re.search(r"(\d\.\d)\s*(?:star|/5|out of 5)", text.lower())
    if rating_match:
        rating = rating_match.group(1)

    # Look for patterns like "(123 reviews)" or "123 Google reviews"
    review_match = re.search(r"(\d{1,5})\s*(?:review|Rating)", text, re.IGNORECASE)
    if review_match:
        review_count = review_match.group(1)

    return rating, review_count


def deep_extract_contact(url: str, niche_keywords: list[str] | None = None) -> dict[str, Any] | None:
    """
    Crawl a business website and extract contact info.
    Returns a lead dict or None.
    """
    log.debug("Deep-extracting: %s", url)
    _polite_delay()

    homepage_html = _fetch_html(url)
    if not homepage_html:
        return None

    soup = BeautifulSoup(homepage_html, "html.parser")

    all_emails: set[str] = set()
    all_phones: set[str] = set()

    # Process homepage
    all_emails |= _extract_emails(homepage_html)
    all_phones |= _extract_phones(homepage_html)

    business_name = _extract_business_name(url, soup)
    rating, review_count = _extract_rating_from_page(homepage_html)

    # Find and crawl internal contact/about pages
    contact_keywords = {"contact", "about", "team", "reach", "get-in-touch"}
    base_domain = _domain_of(url)
    internal_links = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(url, href)
        if _domain_of(full_url) != base_domain:
            continue
        path = urlparse(full_url).path.lower()
        text = a_tag.get_text(strip=True).lower()
        combined = f"{path} {text}"
        if any(kw in combined for kw in contact_keywords):
            if full_url not in internal_links:
                internal_links.append(full_url)

    for link in internal_links[:MAX_PAGES_PER_LEAD - 1]:
        _polite_delay()
        page_html = _fetch_page(link)
        if not page_html:
            continue
        all_emails |= _extract_emails(page_html)
        all_phones |= _extract_phones(page_html)

    best_email = sorted(all_emails)[0] if all_emails else ""
    best_phone = sorted(all_phones, key=len, reverse=True)[0] if all_phones else ""

    return {
        "business_name": business_name,
        "email": best_email,
        "phone": best_phone,
        "website": url,
        "google_rating": rating,
        "review_count": review_count,
        "running_ads": "",  # Will be determined separately
    }


# ──────────────────────────────────────────────
# Deduplication
# ──────────────────────────────────────────────
def _normalise(value: str) -> str:
    return value.strip().lower()


def is_duplicate(lead: dict[str, str], existing: list[dict[str, str]]) -> bool:
    lead_name = _normalise(lead.get("business_name", ""))
    lead_email = _normalise(lead.get("email", ""))
    lead_domain = _domain_of(lead.get("website", ""))

    for existing_lead in existing:
        if lead_name and lead_name == _normalise(existing_lead.get("business_name", "")):
            return True
        if lead_email and "@" in lead_email and lead_email == _normalise(existing_lead.get("email", "")):
            return True
        if lead_domain and lead_domain == _domain_of(existing_lead.get("website", "")):
            return True
    return False


# ──────────────────────────────────────────────
# Relevance Check
# ──────────────────────────────────────────────
def _is_relevant_result(title: str, body: str, url: str, niche_keywords: list[str]) -> bool:
    """Check if a search result is relevant to the target niche."""
    combined = f"{title} {body} {url}".lower()
    return any(kw.lower() in combined for kw in niche_keywords)


# ──────────────────────────────────────────────
# Country Detection Helper
# ──────────────────────────────────────────────
def _get_country_for_city(city: str) -> str:
    """Find which country a city belongs to."""
    for country, cities in TARGET_CITIES.items():
        if city in cities:
            return country
    return "Unknown"


# ──────────────────────────────────────────────
# Main Prospecting Pipeline
# ──────────────────────────────────────────────
def prospect_leads(
    existing_leads: list[dict[str, str]],
    stats: dict[str, Any],
    target_niches: list[str] | None = None,
    target_cities: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    Run the full prospecting pipeline:
      1. Shuffle cities
      2. For each city × niche × query, run the search chain
      3. Deep-extract contact info
      4. Deduplicate
      5. Stop when DAILY_TARGET reached

    Returns a list of new prospect dicts (without scoring — call scorer separately).
    """
    new_leads: list[dict[str, str]] = []
    seen_domains: set[str] = set()
    today = date.today().isoformat()

    # Pre-populate seen domains
    for lead in existing_leads:
        d = _domain_of(lead.get("website", ""))
        if d:
            seen_domains.add(d)

    # Dynamically load targets from self-optimizer
    import self_optimizer
    dynamic_targets = self_optimizer.get_current_targets()
    banned_markets = set(dynamic_targets.get("banned_markets", []))

    # Filter niches if specified
    niches_to_use = dynamic_targets["niches"]
    if target_niches:
        niches_to_use = [n for n in niches_to_use if n["name"] in target_niches]

    # Filter cities if specified
    cities_to_use = target_cities or dynamic_targets["cities"]

    search_sources = [
        ("DuckDuckGo", search_duckduckgo),
        ("Google", search_google),
        ("Bing", search_bing),
    ]

    for cycle in range(1, MAX_RETRY_CYCLES + 1):
        if len(new_leads) >= DAILY_TARGET:
            break

        log.info("── Prospecting cycle %d / %d ──", cycle, MAX_RETRY_CYCLES)

        cities = list(cities_to_use)
        random.shuffle(cities)

        for city in cities:
            if len(new_leads) >= DAILY_TARGET:
                break

            country = _get_country_for_city(city)

            for niche in niches_to_use:
                if len(new_leads) >= DAILY_TARGET:
                    break

                niche_name = niche["name"]
                
                # AGI Autonomy: Skip if market was banned by self-optimizer
                market_key = f"{niche_name} in {city}"
                if market_key in banned_markets:
                    log.warning("Skipping banned dead market: %s", market_key)
                    continue
                    
                niche_keywords = niche["keywords"]
                queries = niche["queries"]

                for query_template in queries:
                    if len(new_leads) >= DAILY_TARGET:
                        break

                    query = query_template.format(niche=niche_name.lower(), city=city)
                    log.info("Searching: %s", query)

                    # Try each source
                    search_results = []
                    for source_name, source_fn in search_sources:
                        stats["sources_tried"] += 1
                        search_results = source_fn(query)
                        if search_results:
                            break
                        _polite_delay()

                    if not search_results:
                        log.warning("All sources returned 0 results for: %s", query)
                        continue

                    # Process results
                    for result in search_results:
                        if len(new_leads) >= DAILY_TARGET:
                            break

                        href = result.get("href", "")
                        if not href:
                            continue

                        domain = _domain_of(href)

                        if domain in SKIP_DOMAINS:
                            continue
                        if domain in seen_domains:
                            stats["duplicates_filtered"] += 1
                            continue

                        # Relevance check
                        title = result.get("title", "")
                        body = result.get("body", "")
                        if not _is_relevant_result(title, body, href, niche_keywords):
                            continue

                        # Competitor tracking for AI FOMO
                        # The first result in the search is usually the #1 ranked competitor
                        top_competitor = "your biggest competitor"
                        if search_results:
                            first_title = search_results[0].get("title", "")
                            if first_title and "Yelp" not in first_title and "BBB" not in first_title:
                                # Clean up the title a bit
                                top_competitor = first_title.split("|")[0].split("-")[0].strip()
                        
                        stats["candidates_found"] += 1

                        # Deep extract
                        lead_data = deep_extract_contact(href, niche_keywords)
                        if not lead_data:
                            continue

                        # Add metadata
                        lead_data["niche"] = niche_name
                        lead_data["city"] = city
                        lead_data["country"] = country
                        lead_data["date_scraped"] = today
                        lead_data["status"] = "New"
                        lead_data["top_competitor"] = top_competitor

                        # Dedup
                        combined = existing_leads + new_leads
                        if is_duplicate(lead_data, combined):
                            stats["duplicates_filtered"] += 1
                            seen_domains.add(domain)
                            continue

                        # Accept
                        seen_domains.add(domain)
                        new_leads.append(lead_data)
                        stats["leads_accepted"] += 1

                        if city not in stats["cities_searched"]:
                            stats["cities_searched"].append(city)

                        log.info(
                            "[+] Prospect #%d: %s (%s, %s)",
                            len(new_leads),
                            lead_data["business_name"],
                            niche_name, city,
                        )

    log.info("Prospecting complete: %d leads found.", len(new_leads))
    return new_leads
