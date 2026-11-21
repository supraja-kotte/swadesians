"""Tests for weather advice rules and endpoints (no network required)."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.weather_service import build_advisories, condition_key

client = TestClient(app)


def test_condition_key_mapping() -> None:
    assert condition_key(0) == "clear"
    assert condition_key(65) == "heavy_rain"
    assert condition_key(999) == "unknown"


def test_heavy_rain_advice() -> None:
    current = {"temperature": 28.0, "feels_like": 30.0, "wind_speed": 10.0}
    daily = [{"rain_chance": 80.0, "rainfall": 20.0}]

    advice = build_advisories(current, daily, "rice")

    assert advice[0]["code"] == "heavy_rain"
    assert advice[0]["severity"] == "warning"
    assert advice[0]["values"]["crop"] == "rice"


def test_heat_and_wind_advice() -> None:
    current = {"temperature": 41.0, "feels_like": 39.0, "wind_speed": 35.0}

    advice = build_advisories(current, [], None)
    codes = {item["code"] for item in advice}

    assert "high_temperature" in codes
    assert "strong_wind" in codes


def test_favorable_advice_when_no_warning() -> None:
    current = {"temperature": 28.0, "feels_like": 29.0, "wind_speed": 8.0}

    advice = build_advisories(current, [{"rain_chance": 10.0, "rainfall": 0.0}], None)

    assert advice == [{"code": "favorable", "severity": "notice", "values": {"crop": ""}}]


def test_weather_requires_a_location() -> None:
    assert client.get("/api/weather").status_code == 422


def test_weather_failure_has_no_demo_fallback(monkeypatch) -> None:
    from app.services import weather_service

    def broken_fetch(latitude, longitude):
        raise RuntimeError("provider down")

    monkeypatch.setattr(weather_service, "fetch_forecast", broken_fetch)
    response = client.get("/api/weather?lat=17.4&lon=78.5")

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]
