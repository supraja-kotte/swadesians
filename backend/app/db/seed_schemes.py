"""Neutral topic IDs for government scheme guidance.

These rows contain no scheme data. They only describe the kinds of questions a
farmer should ask an official source, with the translated advice in the frontend.
They are navigation topics, not demo content.
"""

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.schemes import SchemeTopic

GUIDANCE_TOPICS = [
    ("official", "finding-official-info"),
    ("official", "avoiding-fake-claims"),
    ("eligibility", "checking-eligibility"),
    ("documents", "documents"),
    ("application", "application-steps"),
    ("help", "where-to-ask"),
    ("help", "checking-status"),
]


def seed_guidance_topics() -> None:
    """Insert topic rows once, only when the table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(SchemeTopic.id).limit(1)).first()
        if existing:
            return

        for order, (category, topic_id) in enumerate(GUIDANCE_TOPICS, start=1):
            db.add(
                SchemeTopic(
                    id=topic_id,
                    category=category,
                    sort_order=order,
                    is_demo=False,
                )
            )

        db.commit()
