"""Neutral IDs for demo video entries.

These cards describe no real video, channel or link. They exist only to show
the catalogue layout and the local save-list flow.
"""

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.videos import VideoEntry

DEMO_VIDEOS = [
    ("soil", "demo-video-soil-prep"),
    ("soil", "demo-video-soil-testing"),
    ("water", "demo-video-irrigation"),
    ("water", "demo-video-rain-check"),
    ("crops", "demo-video-seed-selection"),
    ("pests", "demo-video-pest-checks"),
    ("schemes", "demo-video-scheme-info"),
    ("equipment", "demo-video-tool-care"),
]


def seed_demo_videos() -> None:
    """Insert video rows once, only when the table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(VideoEntry.id).limit(1)).first()
        if existing:
            return

        for order, (category, video_id) in enumerate(DEMO_VIDEOS, start=1):
            db.add(
                VideoEntry(
                    id=video_id,
                    category=category,
                    sort_order=order,
                    is_demo=True,
                )
            )

        db.commit()
