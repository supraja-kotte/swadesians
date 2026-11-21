"""Tests for smart farming topics and field notes."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.smart_farming import VALID_SMART_CATEGORIES

client = TestClient(app)


def test_demo_topics_are_seeded_and_labelled() -> None:
    response = client.get("/api/smart-farming/topics")

    assert response.status_code == 200
    topics = response.json()["topics"]
    assert len(topics) >= 6
    assert all(topic["is_demo"] is True for topic in topics)
    assert all(topic["category"] in VALID_SMART_CATEGORIES for topic in topics)


def test_topic_category_filter() -> None:
    water = client.get("/api/smart-farming/topics?category=water").json()["topics"]
    assert len(water) == 1
    assert water[0]["id"] == "irrigation-planning"

    unknown = client.get("/api/smart-farming/topics?category=unknown")
    assert unknown.status_code == 422


def test_field_note_is_saved_unchanged() -> None:
    created = client.post(
        "/api/smart-farming/notes",
        json={
            "field_name": "North field",
            "crop": "Tomato",
            "stage": "Vegetative",
            "observation": "Soil looked dry in the morning.",
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["observation"] == "Soil looked dry in the morning."
    assert body["stage"] == "Vegetative"

    notes = client.get("/api/smart-farming/notes").json()["notes"]
    assert any(note["id"] == body["id"] for note in notes)


def test_field_note_validation() -> None:
    too_short = client.post(
        "/api/smart-farming/notes",
        json={"field_name": "A", "crop": "B"},
    )
    assert too_short.status_code == 422
