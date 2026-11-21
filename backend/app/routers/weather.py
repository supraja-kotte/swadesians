"""Weather API endpoints backed by live Open-Meteo data only."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("")
def get_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    crop: str | None = Query(None, max_length=40, description="Optional crop name"),
) -> dict[str, Any]:
    """Return current weather, forecasts and farm advice for a location."""
    try:
        return weather_service.get_weather(lat, lon, crop)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Live weather is temporarily unavailable. No demo weather is shown.",
        ) from exc


@router.get("/places")
def get_places(name: str = Query(..., min_length=2, max_length=80)) -> dict[str, Any]:
    """Find places for manual location selection."""
    try:
        return {"results": weather_service.search_places(name)}
    except Exception:
        return {"results": [], "error": "Place search is temporarily unavailable"}
