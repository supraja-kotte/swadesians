"""Tests for government scheme guidance topics and personal questions."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.schemes import VALID_SCHEME_CATEGORIES

client = TestClient(app)


def test_demo_topics_are_seeded_and_labelled() -> None:
    response = client.get("/api/schemes/topics")

    assert response.status_code == 200
    topics = response.json()["topics"]
    assert len(topics) >= 7
    assert all(topic["is_demo"] is True for topic in topics)
    assert all(topic["category"] in VALID_SCHEME_CATEGORIES for topic in topics)


def test_topic_category_filter_and_validation() -> None:
    help_topics = client.get("/api/schemes/topics?category=help").json()["topics"]
    assert len(help_topics) == 2
    assert all(topic["category"] == "help" for topic in help_topics)

    unknown = client.get("/api/schemes/topics?category=unknown")
    assert unknown.status_code == 422


def test_question_create_list_and_delete() -> None:
    created = client.post(
        "/api/schemes/questions",
        json={"question": "Which office should I visit for local scheme information?"},
    )
    assert created.status_code == 201
    question_id = created.json()["id"]
    assert created.json()["question"].startswith("Which office")

    questions = client.get("/api/schemes/questions").json()["questions"]
    assert any(item["id"] == question_id for item in questions)

    deleted = client.delete(f"/api/schemes/questions/{question_id}")
    assert deleted.json()["deleted"] is True
    assert question_id not in [item["id"] for item in client.get("/api/schemes/questions").json()["questions"]]


def test_question_validation_and_missing_delete() -> None:
    too_short = client.post("/api/schemes/questions", json={"question": "hi"})
    assert too_short.status_code == 422

    missing = client.delete("/api/schemes/questions/not-a-question")
    assert missing.status_code == 404
