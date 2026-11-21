"""Live mandi price API.

Prices come from the official Agmarknet dataset via data.gov.in. Nothing is
seeded and no price is invented: if the feed is unavailable, the API says so.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services import mandi_service

router = APIRouter(prefix="/marketplace", tags=["marketplace"])
logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "grains",
    "pulses",
    "vegetables",
    "fruits",
    "oils",
    "spices",
    "other",
}


@router.get("/prices")
def list_prices(
    category: str | None = Query(None, max_length=30),
    location: str | None = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Return current wholesale prices for Andhra Pradesh and Telangana."""
    if category and category != "all" and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown category")

    try:
        return mandi_service.get_prices(category=category, location=location, limit=limit)
    except Exception as exc:
        logger.exception("Mandi feed request failed")
        raise HTTPException(
            status_code=503,
            detail="Live mandi prices are temporarily unavailable. No demo prices are shown.",
        ) from exc
