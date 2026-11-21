"""Tests for the optional farmer profile API."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_profile_round_trip() -> None:
    profile_id = "test-profile-roundtrip"
    payload = {
        "state": "Telangana",
        "district": "Hyderabad",
        "crop": "rice",
        "land_size": "2",
        "soil_type": "loam",
        "irrigation": "canal",
        "interests": ["smart", "schemes"],
    }

    saved = client.put(f"/api/profile/{profile_id}", json=payload)
    assert saved.status_code == 200
    assert saved.json()["crop"] == "rice"
    assert saved.json()["interests"] == ["smart", "schemes"]

    loaded = client.get(f"/api/profile/{profile_id}")
    assert loaded.status_code == 200
    assert loaded.json()["district"] == "Hyderabad"


def test_unknown_profile_is_empty() -> None:
    response = client.get("/api/profile/nobody-here")

    assert response.status_code == 200
    assert response.json()["crop"] == ""
    assert response.json()["interests"] == []


def test_profile_validation() -> None:
    response = client.put("/api/profile/bad-input", json={"crop": "x" * 100})

    assert response.status_code == 422
