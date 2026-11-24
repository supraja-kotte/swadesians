"""Natural-language answers for the voice assistant.

The browser sends speech through the device recogniser and then sends the
recognised text here. The API key is read from the backend environment only.
Answers are plain prose in the farmer's language, never command IDs, codes or
binary/technical notation.

Supported providers:
  * openai  — OpenAI-compatible chat completions (default)
  * gemini  — Google Gemini generateContent

Both use Python's standard library, so no new runtime dependency is needed.
"""

import json
import time
from collections import defaultdict, deque
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from ..config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_PROVIDER,
    AI_TIMEOUT_SECONDS,
    SUPPORTED_VOICE_LANGUAGES,
)

ASK_LIMIT = 20
ASK_WINDOW_SECONDS = 60
MAX_ANSWER_CHARS = 1500

_ask_times: defaultdict[str, deque[float]] = defaultdict(deque)


class AIUnavailableError(Exception):
    """No server-side key is configured."""


class AIProviderError(Exception):
    """The provider call failed or returned an unusable answer."""


class AskRateLimited(Exception):
    """Too many questions from one client in the time window."""


def is_configured() -> bool:
    return bool(AI_API_KEY.strip())


def clear_ask_attempts() -> None:
    """Test helper: forget all per-client request timestamps."""
    _ask_times.clear()


def check_ask_allowed(client_host: str) -> None:
    """Small in-process guard against accidental API-key abuse."""
    now = time.monotonic()
    history = _ask_times[client_host or "unknown"]
    while history and now - history[0] > ASK_WINDOW_SECONDS:
        history.popleft()
    if len(history) >= ASK_LIMIT:
        raise AskRateLimited
    history.append(now)


def _system_prompt(language: str) -> str:
    language_name = SUPPORTED_VOICE_LANGUAGES[language]
    return (
        "You are the AgriGuide voice assistant for Indian farmers. "
        f"Answer only in natural, spoken {language_name}. "
        "Use short, simple sentences that sound like a helpful person talking, "
        "not a machine. Do not use command IDs, codes, bullet symbols, JSON, "
        "binary numbers or technical notation. "
        "Talk only about farming, crops, soil, water, weather, equipment, "
        "markets, livestock and government scheme guidance. "
        "For other topics, politely say you can help with farming questions. "
        "Never invent prices, sellers, scheme names, benefit amounts or "
        "guaranteed yields. Tell the farmer to confirm current rules with the "
        "official source or local agriculture office. "
        "Keep the answer under 120 words."
    )


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=AI_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise AIProviderError(str(exc)) from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise AIProviderError("Provider returned invalid JSON") from exc


def _clean_answer(text: str) -> str:
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        raise AIProviderError("Provider returned an empty answer")
    if len(cleaned) > MAX_ANSWER_CHARS:
        cleaned = cleaned[:MAX_ANSWER_CHARS].rsplit(" ", 1)[0] + "…"
    return cleaned


def _ask_openai(text: str, language: str) -> str:
    body = _post_json(
        f"{AI_BASE_URL}/chat/completions",
        {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": _system_prompt(language)},
                {"role": "user", "content": text},
            ],
            "temperature": 0.4,
            "max_tokens": 400,
        },
        {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderError("Unexpected chat completions response") from exc
    return _clean_answer(content)


def _ask_gemini(text: str, language: str) -> str:
    body = _post_json(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(AI_MODEL, safe='')}:generateContent",
        {
            "systemInstruction": {"parts": [{"text": _system_prompt(language)}]},
            "contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
        },
        {
            "x-goog-api-key": AI_API_KEY,
            "Content-Type": "application/json",
        },
    )
    try:
        content = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderError("Unexpected Gemini response") from exc
    return _clean_answer(content)


def ask_agriculture_question(text: str, language: str) -> str:
    """Return a natural-language farming answer in the requested language."""
    if not is_configured():
        raise AIUnavailableError("AI key is not configured")
    if language not in SUPPORTED_VOICE_LANGUAGES:
        raise ValueError("Unsupported language")

    if AI_PROVIDER == "gemini":
        return _ask_gemini(text, language)
    return _ask_openai(text, language)
