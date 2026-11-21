"""Tests for the voice command catalogue and its keyless fallback."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.assistant import VALID_COMMAND_CATEGORIES

client = TestClient(app)


def test_navigation_commands_are_seeded_without_demo_labels() -> None:
    response = client.get("/api/assistant/commands")

    assert response.status_code == 200
    commands = response.json()["commands"]
    assert len(commands) >= 11
    assert all(command["is_demo"] is False for command in commands)
    assert all(command["category"] in VALID_COMMAND_CATEGORIES for command in commands)


def test_category_filter_and_validation() -> None:
    reading = client.get("/api/assistant/commands?category=reading").json()["commands"]
    assert len(reading) == 2
    assert all(command["category"] == "reading" for command in reading)

    unknown = client.get("/api/assistant/commands?category=unknown")
    assert unknown.status_code == 422


def test_keyless_assistant_does_not_invent_answers() -> None:
    # Without a server-side key the endpoint refuses rather than making up a
    # reply. Fixed commands still work; see the command tests above.
    response = client.post(
        "/api/assistant/ask",
        json={"text": "Will it rain tomorrow?", "language": "en"},
    )
    assert response.status_code == 503
    assert "answer" not in response.json()
