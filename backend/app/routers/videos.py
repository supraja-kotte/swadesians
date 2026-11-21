"""Video catalogue API (demo entries) and a purely local save list."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.videos import SavedVideo, VideoEntry
from app.schemas.videos import VALID_VIDEO_CATEGORIES

router = APIRouter(prefix="/videos", tags=["videos"])


def serialize_entry(row: VideoEntry) -> dict[str, Any]:
    return {
        "id": row.id,
        "category": row.category,
        "sort_order": row.sort_order,
        "is_demo": row.is_demo,
    }


@router.get("/entries")
def list_entries(category: str | None = Query(None, max_length=30)) -> dict[str, Any]:
    """Return neutral demo video IDs, optionally filtered by category."""
    with SessionLocal() as db:
        statement = select(VideoEntry).order_by(VideoEntry.sort_order.asc())

        if category and category != "all":
            if category not in VALID_VIDEO_CATEGORIES:
                raise HTTPException(status_code=422, detail="Unknown category")
            statement = statement.where(VideoEntry.category == category)

        rows = db.execute(statement).scalars().all()
        return {"entries": [serialize_entry(row) for row in rows]}


@router.get("/saved")
def list_saved() -> dict[str, Any]:
    """Return the IDs the farmer saved on this device."""
    with SessionLocal() as db:
        rows = db.execute(select(SavedVideo.video_id)).scalars().all()
        return {"ids": rows}


@router.post("/{video_id}/save")
def save_video(video_id: str) -> dict[str, Any]:
    with SessionLocal() as db:
        entry = db.get(VideoEntry, video_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Video entry not found")

        if db.get(SavedVideo, video_id) is None:
            db.add(SavedVideo(video_id=video_id))
            db.commit()

        return {"video_id": video_id, "saved": True}


@router.delete("/{video_id}/save")
def remove_saved_video(video_id: str) -> dict[str, Any]:
    with SessionLocal() as db:
        row = db.get(SavedVideo, video_id)
        if row is not None:
            db.delete(row)
            db.commit()

        return {"video_id": video_id, "saved": False}
