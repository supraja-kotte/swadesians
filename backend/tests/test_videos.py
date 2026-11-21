"""Tests for demo video entries and the local save list."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.videos import VALID_VIDEO_CATEGORIES

client = TestClient(app)


def test_demo_entries_are_seeded_and_labelled() -> None:
    response = client.get("/api/videos/entries")

    assert response.status_code == 200
    entries = response.json()["entries"]
    assert len(entries) >= 8
    assert all(entry["is_demo"] is True for entry in entries)
    assert all(entry["category"] in VALID_VIDEO_CATEGORIES for entry in entries)


def test_category_filter_and_validation() -> None:
    water = client.get("/api/videos/entries?category=water").json()["entries"]
    assert len(water) == 2
    assert all(entry["category"] == "water" for entry in water)

    unknown = client.get("/api/videos/entries?category=unknown")
    assert unknown.status_code == 422


def test_save_and_remove_flow() -> None:
    saved = client.post("/api/videos/demo-video-soil-prep/save")
    assert saved.status_code == 200
    assert saved.json()["saved"] is True

    ids = client.get("/api/videos/saved").json()["ids"]
    assert "demo-video-soil-prep" in ids

    # Saving twice must not create duplicates.
    client.post("/api/videos/demo-video-soil-prep/save")
    assert client.get("/api/videos/saved").json()["ids"].count("demo-video-soil-prep") == 1

    removed = client.delete("/api/videos/demo-video-soil-prep/save")
    assert removed.json()["saved"] is False
    assert "demo-video-soil-prep" not in client.get("/api/videos/saved").json()["ids"]


def test_saving_unknown_entry_fails() -> None:
    missing = client.post("/api/videos/not-a-video/save")
    assert missing.status_code == 404
