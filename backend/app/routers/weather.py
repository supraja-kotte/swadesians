"""Weather API endpoints."""

from typing import Any

from fastapi import APIRouter, Query

from app.services import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("")
def get_weather(
    lat: float | None = Query(None, ge=-90, le=90, description="Latitude"),
    lon: float | None = Query(None, ge=-180, le=180, description="Longitude"),
    crop: str | None = Query(None, max_length=40, description="Optional crop name"),
) -> dict[str, Any]:
    """Return current weather, forecasts and farm advice.

    Without coordinates this returns clearly labelled demo data, so the UI
    works even before location permission is granted.
    """
    if lat is None or lon is None:
        return weather_service.demo_weather(crop)

    try:
        return weather_service.get_weather(lat, lon, crop)
    except Exception:
        # Never break the page because an outside service is unavailable.
        data = weather_service.demo_weather(crop)
        data["source"] = "Demo fallback — live weather unavailable"
        return data


@router.get("/places")
def get_places(name: str = Query(..., min_length=2, max_length=80)) -> dict[str, Any]:
    """Find places for manual location selection."""
    try:
        return {"results": weather_service.search_places(name)}
    except Exception:
        return {"results": [], "error": "Place search is temporarily unavailable"}
