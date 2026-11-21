"""Weather service using Open-Meteo.

Open-Meteo is free for non-commercial use and needs no API key. All network
calls happen here on the backend; the browser never talks to Open-Meteo
directly. A short cache avoids repeated calls for the same location.
"""

import time
from typing import Any

import httpx2

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
CACHE_TTL_SECONDS = 600
REQUEST_TIMEOUT = 20

# WMO weather codes published by Open-Meteo. We map them to simple keys that
# the frontend can translate into any supported language.
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("clear", "Clear sky"),
    1: ("mainly_clear", "Mainly clear"),
    2: ("partly_cloudy", "Partly cloudy"),
    3: ("cloudy", "Overcast"),
    45: ("fog", "Fog"),
    48: ("fog", "Depositing rime fog"),
    51: ("drizzle", "Light drizzle"),
    53: ("drizzle", "Moderate drizzle"),
    55: ("drizzle", "Dense drizzle"),
    61: ("rain", "Slight rain"),
    63: ("rain", "Moderate rain"),
    65: ("heavy_rain", "Heavy rain"),
    71: ("snow", "Slight snow"),
    73: ("snow", "Moderate snow"),
    75: ("snow", "Heavy snow"),
    80: ("rain", "Slight rain showers"),
    81: ("rain", "Moderate rain showers"),
    82: ("heavy_rain", "Violent rain showers"),
    95: ("thunderstorm", "Thunderstorm"),
    96: ("thunderstorm", "Thunderstorm with hail"),
    99: ("thunderstorm", "Thunderstorm with heavy hail"),
}

_cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}


def condition_key(code: int | None) -> str:
    """Return a simple, translatable key for a WMO weather code."""
    if code is None:
        return "unknown"
    return WMO_CODES.get(int(code), ("unknown", "Unknown"))[0]


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fetch_forecast(latitude: float, longitude: float) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m,wind_direction_10m,is_day"
        ),
        "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code",
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,"
            "precipitation_sum,precipitation_probability_max"
        ),
        "timezone": "auto",
        "forecast_days": 7,
    }
    response = httpx2.get(FORECAST_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _start_hour_index(hourly: dict[str, Any], current_time: str) -> int:
    """Find the first hourly entry at or after the current hour."""
    target = current_time[:13]
    for index, stamp in enumerate(hourly.get("time", [])):
        if str(stamp)[:13] >= target:
            return index
    return 0


def normalize_forecast(raw: dict[str, Any], latitude: float, longitude: float, crop: str | None) -> dict[str, Any]:
    """Turn the raw API response into a small, predictable shape for the UI."""
    current_raw = raw.get("current", {})
    hourly_raw = raw.get("hourly", {})
    daily_raw = raw.get("daily", {})
    current_time = str(current_raw.get("time", ""))

    current = {
        "time": current_time,
        "temperature": _number(current_raw.get("temperature_2m")),
        "feels_like": _number(current_raw.get("apparent_temperature"), _number(current_raw.get("temperature_2m"))),
        "humidity": _number(current_raw.get("relative_humidity_2m")),
        "precipitation": _number(current_raw.get("precipitation")),
        "wind_speed": _number(current_raw.get("wind_speed_10m")),
        "wind_direction": _number(current_raw.get("wind_direction_10m")),
        "weather_code": current_raw.get("weather_code"),
        "condition_key": condition_key(current_raw.get("weather_code")),
        "is_day": bool(current_raw.get("is_day", 1)),
    }

    start = _start_hour_index(hourly_raw, current_time)
    hourly = []
    for index in range(start, min(start + 12, len(hourly_raw.get("time", [])))):
        hourly.append(
            {
                "time": str(hourly_raw["time"][index])[11:16],
                "temperature": _number(hourly_raw.get("temperature_2m", [None] * len(hourly_raw.get("time", [])))[index]),
                "rain_chance": _number(hourly_raw.get("precipitation_probability", [None] * len(hourly_raw.get("time", [])))[index]),
                "precipitation": _number(hourly_raw.get("precipitation", [None] * len(hourly_raw.get("time", [])))[index]),
                "condition_key": condition_key(
                    hourly_raw.get("weather_code", [None] * len(hourly_raw.get("time", [])))[index]
                ),
            }
        )

    daily = []
    for index, date in enumerate(daily_raw.get("time", [])[:7]):
        daily.append(
            {
                "date": str(date),
                "condition_key": condition_key(
                    daily_raw.get("weather_code", [None] * len(daily_raw.get("time", [])))[index]
                ),
                "max": _number(daily_raw.get("temperature_2m_max", [None] * len(daily_raw.get("time", [])))[index]),
                "min": _number(daily_raw.get("temperature_2m_min", [None] * len(daily_raw.get("time", [])))[index]),
                "rain_chance": _number(
                    daily_raw.get("precipitation_probability_max", [None] * len(daily_raw.get("time", [])))[index]
                ),
                "rainfall": _number(daily_raw.get("precipitation_sum", [None] * len(daily_raw.get("time", [])))[index]),
                "sunrise": str(daily_raw.get("sunrise", [None] * len(daily_raw.get("time", [])))[index] or "")[-5:],
                "sunset": str(daily_raw.get("sunset", [None] * len(daily_raw.get("time", [])))[index] or "")[-5:],
            }
        )

    return {
        "is_demo": False,
        "source": "Open-Meteo",
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": raw.get("timezone", "auto"),
            "name": None,
        },
        "crop": crop,
        "current": current,
        "hourly": hourly,
        "daily": daily,
        "advisories": build_advisories(current, daily, crop),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def build_advisories(current: dict[str, Any], daily: list[dict[str, Any]], crop: str | None) -> list[dict[str, Any]]:
    """Create cautious, practical farm suggestions from forecast numbers.

    The wording lives in the frontend so it can be translated. Here we only
    decide which advice applies and include the numbers it needs.
    """
    max_chance = max((day["rain_chance"] for day in daily), default=0.0)
    total_rain = sum(day["rainfall"] for day in daily)
    temperature = current.get("temperature", 0.0)
    feels_like = current.get("feels_like", temperature)
    wind = current.get("wind_speed", 0.0)

    advisories: list[dict[str, Any]] = []

    if max_chance >= 70 or total_rain >= 50:
        advisories.append(
            {
                "code": "heavy_rain",
                "severity": "warning",
                "values": {
                    "chance": int(max_chance),
                    "rainfall": round(total_rain, 1),
                    "crop": crop or "",
                },
            }
        )
    elif max_chance >= 40 or total_rain >= 10:
        advisories.append(
            {
                "code": "rain_likely",
                "severity": "notice",
                "values": {
                    "chance": int(max_chance),
                    "rainfall": round(total_rain, 1),
                    "crop": crop or "",
                },
            }
        )

    if feels_like >= 38 or temperature >= 40:
        advisories.append(
            {
                "code": "high_temperature",
                "severity": "warning",
                "values": {"temp": round(feels_like, 1), "crop": crop or ""},
            }
        )

    if wind >= 30:
        advisories.append(
            {
                "code": "strong_wind",
                "severity": "warning",
                "values": {"wind": round(wind, 1), "crop": crop or ""},
            }
        )

    if not advisories:
        advisories.append(
            {
                "code": "favorable",
                "severity": "notice",
                "values": {"crop": crop or ""},
            }
        )

    return advisories


def get_weather(latitude: float, longitude: float, crop: str | None = None) -> dict[str, Any]:
    """Fetch and normalise weather, using a 10-minute in-memory cache."""
    key = (round(latitude, 2), round(longitude, 2))
    cached = _cache.get(key)
    now = time.time()

    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        data = dict(cached[1])
        data["crop"] = crop
        data["advisories"] = build_advisories(data["current"], data["daily"], crop)
        return data

    raw = fetch_forecast(key[0], key[1])
    data = normalize_forecast(raw, key[0], key[1], crop)
    _cache[key] = (now, data)
    return data


def search_places(name: str) -> list[dict[str, Any]]:
    """Look up place names so users can choose location manually."""
    response = httpx2.get(
        GEOCODE_URL,
        params={"name": name, "count": 5, "language": "en", "format": "json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    results = response.json().get("results", [])

    return [
        {
            "name": item.get("name", ""),
            "admin1": item.get("admin1", ""),
            "country": item.get("country", ""),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        }
        for item in results
    ]


def demo_weather(crop: str | None = None) -> dict[str, Any]:
    """Clearly labelled sample data used when no location or live service exists."""
    current = {
        "time": "Demo",
        "temperature": 31.0,
        "feels_like": 34.0,
        "humidity": 68.0,
        "precipitation": 0.0,
        "wind_speed": 12.0,
        "wind_direction": 210.0,
        "weather_code": 2,
        "condition_key": "partly_cloudy",
        "is_day": 1,
    }
    daily = [
        {
            "date": "Demo day 1",
            "condition_key": "partly_cloudy",
            "max": 33.0,
            "min": 25.0,
            "rain_chance": 45.0,
            "rainfall": 2.4,
            "sunrise": "06:12",
            "sunset": "18:04",
        }
    ] + [
        {
            "date": f"Demo day {index}",
            "condition_key": "rain",
            "max": 30.0,
            "min": 24.0,
            "rain_chance": 55.0,
            "rainfall": 6.0,
            "sunrise": "06:13",
            "sunset": "18:03",
        }
        for index in range(2, 8)
    ]
    hourly = [
        {
            "time": f"{hour:02d}:00",
            "temperature": 28.0 + (hour % 5),
            "rain_chance": 20.0 + hour,
            "precipitation": 0.0,
            "condition_key": "partly_cloudy",
        }
        for hour in range(6, 18)
    ]

    return {
        "is_demo": True,
        "source": "Demo data",
        "location": {"latitude": None, "longitude": None, "timezone": "Demo", "name": "Demo location"},
        "crop": crop,
        "current": current,
        "hourly": hourly,
        "daily": daily,
        "advisories": build_advisories(current, daily, crop),
        "generated_at": "Demo",
    }
