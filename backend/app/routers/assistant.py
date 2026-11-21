"""Voice assistant commands and optional natural-language answers.

Fixed commands keep working without any key. When a server-side AI key is
configured, free-form farming questions are answered in plain prose in the
farmer's language. The key is never sent to the browser.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select

from app.config import AI_PROVIDER, SUPPORTED_VOICE_LANGUAGES
from app.db.connection import SessionLocal
from app.models.assistant import VoiceCommand
from app.schemas.assistant import AskIn, VALID_COMMAND_CATEGORIES
from app.services.ai import (
    AIProviderError,
    AIUnavailableError,
    AskRateLimited,
    ask_agriculture_question,
    check_ask_allowed,
    is_configured,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])


def serialize_command(row: VoiceCommand) -> dict[str, Any]:
    return {
        "id": row.id,
        "category": row.category,
        "sort_order": row.sort_order,
        "is_demo": row.is_demo,
    }


@router.get("/config")
def assistant_config() -> dict[str, Any]:
    """Tell the browser whether natural-language answers are available."""
    return {"available": is_configured(), "provider": AI_PROVIDER if is_configured() else ""}


@router.post("/ask")
def ask(payload: AskIn, request: Request) -> dict[str, Any]:
    """Answer one farming question in the farmer's own language."""
    if not is_configured():
        raise HTTPException(status_code=503, detail="AI assistant is not configured")

    language = payload.language.strip().lower()
    if language not in SUPPORTED_VOICE_LANGUAGES:
        raise HTTPException(status_code=422, detail="Unsupported language")

    try:
        check_ask_allowed(request.client.host if request.client else "unknown")
    except AskRateLimited as exc:
        raise HTTPException(status_code=429, detail="Too many questions. Try again shortly.") from exc

    try:
        answer = ask_agriculture_question(payload.text.strip(), language)
    except AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail="AI assistant is not configured") from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail="AI service is unavailable") from exc

    return {"answer": answer, "language": language, "provider": AI_PROVIDER}


@router.get("/commands")
def list_commands(category: str | None = Query(None, max_length=30)) -> dict[str, Any]:
    """Return neutral command IDs, optionally filtered by category."""
    with SessionLocal() as db:
        statement = select(VoiceCommand).order_by(VoiceCommand.sort_order.asc())

        if category and category != "all":
            if category not in VALID_COMMAND_CATEGORIES:
                raise HTTPException(status_code=422, detail="Unknown category")
            statement = statement.where(VoiceCommand.category == category)

        rows = db.execute(statement).scalars().all()
        return {"commands": [serialize_command(row) for row in rows]}
