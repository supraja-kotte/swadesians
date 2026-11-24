"""Live mandi prices from the Government of India's data.gov.in feed.

The browser never talks to data.gov.in. This service fetches the official
Agmarknet daily price dataset on the backend, normalises it and caches it for a
short time. When the feed is unavailable it raises an error: the app shows an
honest message instead of making up prices.
"""

import hashlib
import time
from datetime import datetime
from typing import Any

import httpx2

from .. import config

RESOURCE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
CACHE_TTL_SECONDS = 1800
REQUEST_TIMEOUT = 30
DEFAULT_STATES = ("Andhra Pradesh", "Telangana")
SOURCE_NAME = "Agmarknet daily mandi prices, Government of India (data.gov.in)"
# data.gov.in rejects requests without a normal browser-style User-Agent.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

# The feed uses its own commodity names. Group them into the app's simple
# categories by keyword; anything unmatched stays in "other".
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "spices": ("turmeric", "coriander", "cumin", "cum in", "cardamom", "clove", "fenugreek", "pepper", "ginger", "garlic"),
    "pulses": ("gram", "toor", "tur ", "moong", "urad", "masoor", "chana", "dal", "pulse", "bean"),
    "oils": ("groundnut", "mustard", "sesame", "sunflower", "soyabean", "soybean", "castor", "coconut", "oil"),
    "fruits": ("mango", "banana", "apple", "orange", "grape", "papaya", "guava", "lemon", "pineapple", "melon", "mosambi"),
    "grains": ("paddy", "rice", "wheat", "maize", "jowar", "bajra", "ragi", "barley", "millets"),
    "vegetables": ("onion", "tomato", "potato", "brinjal", "chilli", "cabbage", "cauliflower", "okra", "bhindi", "cucumber", "kheera", "pumpkin", "beetroot", "carrot", "radish", "peas", "gourd"),
}

_CACHE: dict[Any, tuple[float, dict[str, Any]]] = {}


def _category(commodity: str) -> str:
    text = f" {commodity.lower()} "
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in text for word in keywords):
            return category
    return "other"


def _arrival_date(value: str) -> str:
    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except (TypeError, ValueError):
            continue
    return str(value or "")


def _price(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalise(record: dict[str, Any], fetched_at: str) -> dict[str, Any]:
    state = str(record.get("state") or "").strip()
    district = str(record.get("district") or "").strip()
    market = str(record.get("market") or "").strip()
    commodity = str(record.get("commodity") or "").strip()
    variety = str(record.get("variety") or "").strip()
    arrival = _arrival_date(str(record.get("arrival_date") or ""))
    identity = "|".join((state, district, market, commodity, variety, arrival))

    return {
        "id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        "state": state,
        "district": district,
        "market": market,
        "commodity": commodity,
        "variety": variety,
        "grade": str(record.get("grade") or "").strip(),
        "category": _category(commodity),
        "arrival_date": arrival,
        "min_price": _price(record.get("min_price")),
        "max_price": _price(record.get("max_price")),
        "modal_price": _price(record.get("modal_price")),
        "price_unit": "INR per quintal",
        "source": SOURCE_NAME,
        "fetched_at": fetched_at,
    }


def _fetch_state(state: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "api-key": config.DATA_GOV_API_KEY,
        "format": "json",
        "limit": str(limit),
        "filters[state]": state,
    }
    response = httpx2.get(
        RESOURCE_URL,
        params=params,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "ok":
        raise RuntimeError("Mandi feed returned an error status")
    return payload.get("records") or []


def get_prices(
    category: str | None = None,
    location: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Return current official prices for Andhra Pradesh and Telangana."""
    cache_key = (category or "", (location or "").strip().lower(), limit)
    cached = _CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    fetched_at = datetime.now().astimezone().isoformat(timespec="seconds")
    records: list[dict[str, Any]] = []
    for state in DEFAULT_STATES:
        records.extend(_fetch_state(state, min(limit * 4, 150)))

    prices = [_normalise(record, fetched_at) for record in records]

    if category and category != "all":
        prices = [item for item in prices if item["category"] == category]

    term = (location or "").strip().lower()
    if term:
        prices = [
            item
            for item in prices
            if term in item["district"].lower()
            or term in item["market"].lower()
            or term in item["state"].lower()
        ]

    prices.sort(key=lambda item: (item["arrival_date"], item["market"]), reverse=True)

    result = {
        "prices": prices[:limit],
        "is_live": True,
        "source": SOURCE_NAME,
        "updated_at": fetched_at,
        "states": list(DEFAULT_STATES),
        "matched": len(prices),
    }
    _CACHE[cache_key] = (now, result)
    return result
