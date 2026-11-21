"""Tests for the verified official scheme-link directory."""

from urllib.parse import urlparse

from fastapi.testclient import TestClient

from app.db.seed_scheme_links import VERIFIED_ON, is_official_url
from app.main import app

client = TestClient(app)


def test_verified_links_are_seeded_and_official() -> None:
    response = client.get("/api/schemes/links")
    assert response.status_code == 200

    links = response.json()["links"]
    assert len(links) >= 12
    assert any(item["level"] == "central" for item in links)
    assert any(item["state"] == "Andhra Pradesh" for item in links)
    assert any(item["state"] == "Telangana" for item in links)

    for item in links:
        assert item["url"].startswith("https://")
        assert item["sourceDomain"] == urlparse(item["url"]).hostname
        assert item["verifiedOn"] == VERIFIED_ON
        assert item["level"] in {"central", "state"}
        # The directory stores pointers only, never scheme claims.
        assert set(item) == {
            "id",
            "name",
            "level",
            "state",
            "url",
            "sourceDomain",
            "verifiedOn",
        }


def test_link_filters_and_validation() -> None:
    central = client.get("/api/schemes/links?level=central").json()["links"]
    assert central and all(item["level"] == "central" for item in central)

    state = client.get("/api/schemes/links?state=Telangana").json()["links"]
    assert state and all(item["state"] == "Telangana" for item in state)

    both = client.get(
        "/api/schemes/links?level=state&state=Andhra%20Pradesh"
    ).json()["links"]
    assert both and all(
        item["level"] == "state" and item["state"] == "Andhra Pradesh"
        for item in both
    )

    assert client.get("/api/schemes/links?level=unknown").status_code == 422
    assert client.get("/api/schemes/links?state=unknown").status_code == 422


def test_only_government_domains_are_accepted() -> None:
    assert is_official_url("https://pmkisan.gov.in/") is True
    assert is_official_url("https://spsnellore.ap.gov.in/agriculture") is True
    assert is_official_url("http://pmkisan.gov.in/") is False
    assert is_official_url("https://pmkisan.gov.in.evil.example/") is False
    assert is_official_url("https://example.com/scheme") is False
