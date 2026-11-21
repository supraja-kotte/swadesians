"""Smart farming API: generic guidance topics and verified YouTube videos.

There is deliberately no prediction, scoring or diagnosis endpoint. Video rows
hold only neutral IDs, categories and public URLs; all farmer-facing wording
lives in the frontend i18n files.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.smart_farming import FieldNote, SmartTopic, SmartVideo
from app.schemas.smart_farming import FieldNoteIn, VALID_SMART_CATEGORIES

router = APIRouter(prefix="/smart-farming", tags=["smart-farming"])


def serialize_topic(row: SmartTopic) -> dict[str, Any]:
    return {
        "id": row.id,
        "category": row.category,
        "sort_order": row.sort_order,
        "is_demo": row.is_demo,
    }


def serialize_video(row: SmartVideo) -> dict[str, Any]:
    return {
        "id": row.id,
        "category": row.category,
        "url": row.url,
        "sort_order": row.sort_order,
        "is_demo": row.is_demo,
    }


def serialize_note(row: FieldNote) -> dict[str, Any]:
    return {
        "id": row.id,
        "field_name": row.field_name,
        "crop": row.crop,
        "stage": row.stage,
        "observation": row.observation,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/topics")
def list_topics(category: str | None = Query(None, max_length=30)) -> dict[str, Any]:
    """Return neutral topic IDs, optionally filtered by category."""
    with SessionLocal() as db:
        statement = select(SmartTopic).order_by(SmartTopic.sort_order.asc())

        if category and category != "all":
            if category not in VALID_SMART_CATEGORIES:
                raise HTTPException(status_code=422, detail="Unknown category")
            statement = statement.where(SmartTopic.category == category)

        rows = db.execute(statement).scalars().all()
        return {"topics": [serialize_topic(row) for row in rows]}


@router.get("/videos")
def list_videos(category: str | None = Query(None, max_length=30)) -> dict[str, Any]:
    """Return verified video IDs, categories and URLs, optionally filtered."""
    with SessionLocal() as db:
        statement = select(SmartVideo).order_by(SmartVideo.sort_order.asc())

        if category and category != "all":
            if category not in VALID_SMART_CATEGORIES:
                raise HTTPException(status_code=422, detail="Unknown category")
            statement = statement.where(SmartVideo.category == category)

        rows = db.execute(statement).scalars().all()
        return {"videos": [serialize_video(row) for row in rows]}


@router.get("/notes")
def list_notes(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    """Return saved field notes, newest first. No analysis is performed."""
    with SessionLocal() as db:
        rows = db.execute(
            select(FieldNote).order_by(FieldNote.created_at.desc()).limit(limit)
        ).scalars().all()
        return {"notes": [serialize_note(row) for row in rows]}


@router.post("/notes", status_code=201)
def create_note(payload: FieldNoteIn) -> dict[str, Any]:
    """Save a farmer's own observation exactly as written."""
    with SessionLocal() as db:
        row = FieldNote(
            id=uuid4().hex,
            field_name=payload.field_name.strip(),
            crop=payload.crop.strip(),
            stage=payload.stage.strip(),
            observation=payload.observation.strip(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return serialize_note(row)
