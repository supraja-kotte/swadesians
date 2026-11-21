"""Tests for the optional natural-language assistant endpoint."""

import json

from fastapi.testclient import TestClient

import app.routers.assistant as assistant_router
import app.services.ai as ai_service
from app.main import app

client = TestClient(app)

OPENAI_REPLY = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "  Check the soil first.   Then add compost and water in the morning.  ",
            }
        }
    ]
}


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self._body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _configure(monkeypatch, reply: dict) -> list:
    calls: list = []

    def fake_urlopen(request, timeout=None):
        calls.append(
            {
                "url": request.full_url,
                "headers": dict(request.header_items()),
                "body": json.loads(request.data.decode("utf-8")),
            }
        )
        return FakeResponse(reply)

    monkeypatch.setattr(ai_service, "AI_API_KEY", "test-only-key")
    monkeypatch.setattr(assistant_router, "is_configured", lambda: True)
    monkeypatch.setattr(ai_service, "is_configured", lambda: True)
    monkeypatch.setattr(ai_service, "urlopen", fake_urlopen)
    ai_service.clear_ask_attempts()
    return calls


def test_config_and_ask_without_key() -> None:
    config = client.get("/api/assistant/config")
    assert config.status_code == 200
    assert config.json()["available"] is False

    response = client.post(
        "/api/assistant/ask", json={"text": "How do I improve my soil?", "language": "en"}
    )
    assert response.status_code == 503


def test_natural_language_answer_is_plain_prose(monkeypatch) -> None:
    calls = _configure(monkeypatch, OPENAI_REPLY)

    response = client.post(
        "/api/assistant/ask",
        json={"text": "How do I improve my soil?", "language": "te"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "te"
    assert body["provider"] == "openai"
    assert body["answer"] == "Check the soil first. Then add compost and water in the morning."
    assert "choices" not in body and "token" not in str(body).lower()
    assert "test-only-key" not in str(body)

    assert len(calls) == 1
    system_text = calls[0]["body"]["messages"][0]["content"]
    assert "Telugu" in system_text
    assert "natural, spoken Telugu" in system_text
    assert "Do not use command IDs" in system_text


def test_validation_and_rate_limit(monkeypatch) -> None:
    _configure(monkeypatch, OPENAI_REPLY)

    assert client.post("/api/assistant/ask", json={"text": "a", "language": "en"}).status_code == 422
    assert client.post(
        "/api/assistant/ask", json={"text": "A farming question?", "language": "zz"}
    ).status_code == 422

    for _ in range(ai_service.ASK_LIMIT):
        assert client.post(
            "/api/assistant/ask", json={"text": "A farming question?", "language": "en"}
        ).status_code == 200

    blocked = client.post(
        "/api/assistant/ask", json={"text": "One more question?", "language": "en"}
    )
    assert blocked.status_code == 429
    ai_service.clear_ask_attempts()
