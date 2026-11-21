"""Community API: questions, replies, reports, local media and moderation.

Reading hidden content and changing a status require an administrator token.
Farmer posting, replying, uploading and reporting stay open.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.connection import SessionLocal
from app.dependencies import require_admin, require_admin_value
from app.models.community import CommunityMedia, CommunityPost, CommunityReply
from app.schemas.community import ModerationIn, PostIn, ReplyIn, VALID_CATEGORIES
from app.services.uploads import (
    UploadError,
    UploadRateLimited,
    check_upload_allowed,
    save_upload,
    validate_media_ref,
)

router = APIRouter(prefix="/community", tags=["community"])


def serialize_post(
    row: CommunityPost,
    reply_count: int = 0,
    media: CommunityMedia | None = None,
) -> dict[str, Any]:
    return {
        "id": row.id,
        "author": row.author,
        "language": row.language,
        "category": row.category,
        "title": row.title,
        "body": row.body,
        "is_demo": row.is_demo,
        "status": row.status,
        "reports": row.reports,
        "reply_count": reply_count,
        "media": (
            {"path": media.media_path, "kind": media.media_kind, "name": media.media_name}
            if media
            else None
        ),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def media_for_posts(db: Session, post_ids: list[str]) -> dict[str, CommunityMedia]:
    """Fetch all attachments for a page of posts in one query."""
    if not post_ids:
        return {}
    rows = db.execute(
        select(CommunityMedia).where(CommunityMedia.post_id.in_(post_ids))
    ).scalars().all()
    return {row.post_id: row for row in rows}


def media_for_post(db: Session, post_id: str) -> CommunityMedia | None:
    return db.execute(
        select(CommunityMedia).where(CommunityMedia.post_id == post_id)
    ).scalars().first()


def serialize_reply(row: CommunityReply) -> dict[str, Any]:
    return {
        "id": row.id,
        "post_id": row.post_id,
        "author": row.author,
        "language": row.language,
        "body": row.body,
        "is_demo": row.is_demo,
        "status": row.status,
        "reports": row.reports,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/posts")
def list_posts(
    request: Request,
    category: str | None = Query(None, max_length=30),
    include_hidden: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Return newest questions first, with reply counts."""
    if include_hidden:
        require_admin_value(request)

    with SessionLocal() as db:
        statement = (
            select(
                CommunityPost,
                func.count(CommunityReply.id).label("reply_count"),
            )
            .outerjoin(
                CommunityReply,
                (CommunityReply.post_id == CommunityPost.id)
                & (CommunityReply.status == "published"),
            )
            .group_by(CommunityPost.id)
            .order_by(CommunityPost.created_at.desc())
        )

        if not include_hidden:
            statement = statement.where(CommunityPost.status == "published")
        if category and category != "all":
            statement = statement.where(CommunityPost.category == category)

        rows = db.execute(statement.limit(limit)).all()
        media = media_for_posts(db, [row.id for row, _ in rows])
        return {
            "posts": [serialize_post(row, count, media.get(row.id)) for row, count in rows]
        }


@router.post("/upload")
def upload_media(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
    """Store one photo or video locally and return metadata for a post."""
    try:
        check_upload_allowed(request.client.host if request.client else "unknown")
    except UploadRateLimited as exc:
        raise HTTPException(
            status_code=429, detail="Too many uploads. Try again shortly."
        ) from exc

    try:
        return save_upload(file)
    except UploadError as exc:
        if exc.code == "large":
            raise HTTPException(status_code=413, detail="File is too large") from exc
        raise HTTPException(status_code=415, detail="Unsupported file type") from exc


@router.post("/posts", status_code=201)
def create_post(payload: PostIn) -> dict[str, Any]:
    if payload.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown category")

    wants_media = any([payload.media_path, payload.media_kind, payload.media_name])
    if wants_media and not validate_media_ref(
        payload.media_path, payload.media_kind, payload.media_name
    ):
        raise HTTPException(status_code=422, detail="Invalid media reference")

    row = CommunityPost(
        id=uuid4().hex,
        author=payload.author.strip() or "Farmer",
        language=payload.language,
        category=payload.category,
        title=payload.title.strip(),
        body=payload.body.strip(),
        is_demo=False,
    )
    with SessionLocal() as db:
        db.add(row)
        db.flush()
        if wants_media:
            db.add(
                CommunityMedia(
                    id=uuid4().hex,
                    post_id=row.id,
                    media_path=payload.media_path,
                    media_kind=payload.media_kind,
                    media_name=payload.media_name,
                )
            )
        db.commit()
        db.refresh(row)
        return serialize_post(row, 0, media_for_post(db, row.id))


@router.get("/posts/{post_id}")
def get_post(
    post_id: str,
    request: Request,
    include_hidden: bool = Query(False),
) -> dict[str, Any]:
    if include_hidden:
        require_admin_value(request)

    with SessionLocal() as db:
        post = db.get(CommunityPost, post_id)
        if post is None or (post.status == "hidden" and not include_hidden):
            raise HTTPException(status_code=404, detail="Question not found")

        reply_query = select(CommunityReply).where(CommunityReply.post_id == post_id)
        if not include_hidden:
            reply_query = reply_query.where(CommunityReply.status == "published")
        replies = db.execute(reply_query.order_by(CommunityReply.created_at.asc())).scalars().all()

        return {
            "post": serialize_post(post, len(replies), media_for_post(db, post_id)),
            "replies": [serialize_reply(reply) for reply in replies],
        }


@router.post("/posts/{post_id}/replies", status_code=201)
def create_reply(post_id: str, payload: ReplyIn) -> dict[str, Any]:
    with SessionLocal() as db:
        post = db.get(CommunityPost, post_id)
        if post is None or post.status == "hidden":
            raise HTTPException(status_code=404, detail="Question not found")

        row = CommunityReply(
            id=uuid4().hex,
            post_id=post_id,
            author=payload.author.strip() or "Farmer",
            language=payload.language,
            body=payload.body.strip(),
            is_demo=False,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return serialize_reply(row)


@router.post("/posts/{post_id}/report")
def report_post(post_id: str) -> dict[str, Any]:
    with SessionLocal() as db:
        post = db.get(CommunityPost, post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Question not found")
        post.reports += 1
        db.commit()
        return {"reports": post.reports}


@router.post("/replies/{reply_id}/report")
def report_reply(reply_id: str) -> dict[str, Any]:
    with SessionLocal() as db:
        reply = db.get(CommunityReply, reply_id)
        if reply is None:
            raise HTTPException(status_code=404, detail="Reply not found")
        reply.reports += 1
        db.commit()
        return {"reports": reply.reports}


@router.patch("/posts/{post_id}/status")
def set_post_status(
    post_id: str,
    payload: ModerationIn,
    admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    with SessionLocal() as db:
        post = db.get(CommunityPost, post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Question not found")
        post.status = payload.status
        db.commit()
        return {"id": post_id, "status": post.status}


@router.patch("/replies/{reply_id}/status")
def set_reply_status(
    reply_id: str,
    payload: ModerationIn,
    admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    with SessionLocal() as db:
        reply = db.get(CommunityReply, reply_id)
        if reply is None:
            raise HTTPException(status_code=404, detail="Reply not found")
        reply.status = payload.status
        db.commit()
        return {"id": reply_id, "status": reply.status}
