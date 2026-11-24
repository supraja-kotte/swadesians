"""Government scheme guidance, verified official links and personal questions.

There is deliberately no eligibility checker or benefit calculator. The link
directory points to official sources only; it makes no scheme claims.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from ..db.connection import SessionLocal
from ..models.schemes import SchemeLink, SchemeQuestion, SchemeTopic
from ..schemas.schemes import (
    QuestionIn,
    VALID_SCHEME_CATEGORIES,
    VALID_SCHEME_LEVELS,
    VALID_SCHEME_STATES,
)

router = APIRouter(prefix="/schemes", tags=["schemes"])


def serialize_topic(row: SchemeTopic) -> dict[str, Any]:
    return {
        "id": row.id,
        "category": row.category,
        "sort_order": row.sort_order,
        "is_demo": row.is_demo,
    }


def serialize_question(row: SchemeQuestion) -> dict[str, Any]:
    return {
        "id": row.id,
        "question": row.question,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/topics")
def list_topics(category: str | None = Query(None, max_length=30)) -> dict[str, Any]:
    """Return neutral guidance topic IDs, optionally filtered by category."""
    with SessionLocal() as db:
        statement = select(SchemeTopic).order_by(SchemeTopic.sort_order.asc())

        if category and category != "all":
            if category not in VALID_SCHEME_CATEGORIES:
                raise HTTPException(status_code=422, detail="Unknown category")
            statement = statement.where(SchemeTopic.category == category)

        rows = db.execute(statement).scalars().all()
        return {"topics": [serialize_topic(row) for row in rows]}


def serialize_link(row: SchemeLink) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "level": row.level,
        "state": row.state,
        "url": row.url,
        "sourceDomain": row.source_domain,
        "verifiedOn": row.verified_on,
    }


@router.get("/links")
def list_links(
    level: str | None = Query(None, max_length=20),
    state: str | None = Query(None, max_length=40),
) -> dict[str, Any]:
    """Return official government links grouped as central or state schemes."""
    if level and level != "all" and level not in VALID_SCHEME_LEVELS:
        raise HTTPException(status_code=422, detail="Unknown scheme level")
    if state and state != "all" and state not in VALID_SCHEME_STATES:
        raise HTTPException(status_code=422, detail="Unknown state")

    with SessionLocal() as db:
        statement = select(SchemeLink).order_by(
            SchemeLink.sort_order.asc(), SchemeLink.name.asc()
        )
        if level and level != "all":
            statement = statement.where(SchemeLink.level == level)
        if state and state != "all":
            statement = statement.where(SchemeLink.state == state)

        rows = db.execute(statement).scalars().all()
        return {"links": [serialize_link(row) for row in rows]}


@router.get("/questions")
def list_questions(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    """Return the farmer's own questions, newest first. No answers are given."""
    with SessionLocal() as db:
        rows = db.execute(
            select(SchemeQuestion).order_by(SchemeQuestion.created_at.desc()).limit(limit)
        ).scalars().all()
        return {"questions": [serialize_question(row) for row in rows]}


@router.post("/questions", status_code=201)
def create_question(payload: QuestionIn) -> dict[str, Any]:
    with SessionLocal() as db:
        row = SchemeQuestion(id=uuid4().hex, question=payload.question.strip())
        db.add(row)
        db.commit()
        db.refresh(row)
        return serialize_question(row)


@router.delete("/questions/{question_id}")
def delete_question(question_id: str) -> dict[str, Any]:
    with SessionLocal() as db:
        row = db.get(SchemeQuestion, question_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Question not found")
        db.delete(row)
        db.commit()
        return {"id": question_id, "deleted": True}
