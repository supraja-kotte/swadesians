"""Neutral topic IDs for the smart farming guidance library.

The actual explanations are translated in the frontend. These rows contain no
recommendations, predictions or diagnoses — only IDs, categories and order.
"""

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.smart_farming import SmartTopic

DEMO_TOPICS = [
    ("soil", "soil-health"),
    ("water", "irrigation-planning"),
    ("crops", "crop-rotation"),
    ("pests", "pest-prevention"),
    ("records", "record-keeping"),
    ("weather", "weather-planning"),
]


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
