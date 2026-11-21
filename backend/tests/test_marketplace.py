"""Tests for the live mandi price API. The feed is stubbed, never called live."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import mandi_service

client = TestClient(app)

RECORDS = [
    {
        "state": "Andhra Pradesh",
        "district": "Guntur",
        "market": "Guntur APMC",
        "commodity": "Paddy(Common)",
        "variety": "Local",
        "grade": "Local",
        "arrival_date": "21/11/2026",
        "min_price": 2400,
        "max_price": 2500,
        "modal_price": 2450,
    },
    {
        "state": "Telangana",
        "district": "Warangal",
        "market": "Warangal APMC",
        "commodity": "Tomato",
        "variety": "Hybrid",
        "grade": "Local",
        "arrival_date": "21/11/2026",
        "min_price": 1200,
        "max_price": 1800,
        "modal_price": 1500,
    },
]


@pytest.fixture(autouse=True)
def clear_cache():
    mandi_service._CACHE.clear()
    yield
    mandi_service._CACHE.clear()


def stub_fetch(monkeypatch):
    def fake_fetch(state, limit):
        return [row for row in RECORDS if row["state"] == state]

    monkeypatch.setattr(mandi_service, "_fetch_state", fake_fetch)


def test_live_prices_are_normalised(monkeypatch):
    stub_fetch(monkeypatch)
    response = client.get("/api/marketplace/prices")

    assert response.status_code == 200
    body = response.json()
    assert body["is_live"] is True
    assert len(body["prices"]) == 2
    first = body["prices"][0]
    assert first["arrival_date"] == "21/11/2026" or "-" in first["arrival_date"]
    assert first["price_unit"] == "INR per quintal"
    assert "data.gov.in" in first["source"]


def test_category_and_location_filters(monkeypatch):
    stub_fetch(monkeypatch)
    grains = client.get("/api/marketplace/prices?category=grains").json()["prices"]
    assert len(grains) == 1
    assert grains[0]["commodity"] == "Paddy(Common)"

    guntur = client.get("/api/marketplace/prices?location=Guntur").json()["prices"]
    assert len(guntur) == 1
    assert guntur[0]["district"] == "Guntur"


def test_unknown_category_is_rejected():
    assert client.get("/api/marketplace/prices?category=unknown").status_code == 422


def test_feed_failure_is_honest(monkeypatch):
    def broken_fetch(state, limit):
        raise RuntimeError("feed down")

    monkeypatch.setattr(mandi_service, "_fetch_state", broken_fetch)
    response = client.get("/api/marketplace/prices")

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]
