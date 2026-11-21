"""Neutral topic IDs and verified video URLs for smart farming.

The actual explanations are translated in the frontend. Topic rows contain no
recommendations, predictions or diagnoses. Video rows contain only an ID,
category, public YouTube URL and order; titles stay in the frontend i18n.
"""

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.smart_farming import SmartTopic, SmartVideo

DEMO_TOPICS = [
    ("soil", "soil-health"),
    ("water", "irrigation-planning"),
    ("crops", "crop-rotation"),
    ("pests", "pest-prevention"),
    ("records", "record-keeping"),
    ("weather", "weather-planning"),
]


# Every URL below was checked through YouTube's oEmbed endpoint on 2026-11-21.
# The publisher names are shown to farmers only in the translated frontend.
VERIFIED_VIDEOS = [
    (
        "soil-health-campaign",
        "soil",
        "https://www.youtube.com/watch?v=9CKCQHISsLM",
    ),
    (
        "green-manuring",
        "soil",
        "https://www.youtube.com/watch?v=wWolzhA1yV4",
    ),
    (
        "soil-health-card",
        "soil",
        "https://www.youtube.com/watch?v=E0-Dua2eWNQ",
    ),
    (
        "integrated-pest-management",
        "pests",
        "https://www.youtube.com/watch?v=b86Be4pw7HI",
    ),
    (
        "irrigation-water-management",
        "water",
        "https://www.youtube.com/watch?v=GCFCReu2J2o",
    ),
]


def seed_verified_smart_videos() -> None:
    """Insert verified video rows once, only when the table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(SmartVideo.id).limit(1)).first()
        if existing:
            return

        for order, (video_id, category, url) in enumerate(VERIFIED_VIDEOS, start=1):
            db.add(
                SmartVideo(
                    id=video_id,
                    category=category,
                    url=url,
                    sort_order=order,
                    is_demo=False,
                )
            )

        db.commit()


def seed_demo_smart_topics() -> None:
    """Insert topic rows once, only when the table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(SmartTopic.id).limit(1)).first()
        if existing:
            return

        for order, (category, topic_id) in enumerate(DEMO_TOPICS, start=1):
            db.add(
                SmartTopic(
                    id=topic_id,
                    category=category,
                    sort_order=order,
                    is_demo=True,
                )
            )

        db.commit()
