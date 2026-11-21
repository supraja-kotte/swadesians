"""Clearly labelled demo content for the community module.

Nothing here claims to be a real farmer, real advice or a real scheme. Every
row has is_demo=True so the interface can show a visible badge.
"""

from uuid import uuid4

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.community import CommunityPost, CommunityReply

DEMO_POSTS = [
    {
        "id": "demo-post-irrigation",
        "author": "Demo farmer",
        "language": "te",
        "category": "irrigation",
        "title": "వరి పొలంలో నీరు ఎప్పుడు పెట్టాలి?",
        "body": "డెమో ప్రశ్న: వరి పొలంలో నీటిపారుదల సమయం ఎలా నిర్ణయించుకోవాలి? మీ అనుభవాలు పంచుకోండి.",
    },
    {
        "id": "demo-post-weather",
        "author": "Demo farmer",
        "language": "en",
        "category": "weather",
        "title": "How do you decide whether to spray before rain?",
        "body": "Demo question: when rain is forecast, how do you plan spraying? Share general experiences, not product claims.",
    },
    {
        "id": "demo-post-crops",
        "author": "Demo farmer",
        "language": "en",
        "category": "crops",
        "title": "What could cause yellow leaves in tomato plants?",
        "body": "Demo question only — this is not a real crop diagnosis. What do farmers usually check first in this situation?",
    },
    {
        "id": "demo-post-schemes",
        "author": "Demo farmer",
        "language": "te",
        "category": "schemes",
        "title": "సబ్సిడీ సమాచారం ఎక్కడ చూడాలి?",
        "body": "డెమో ప్రశ్న: సబ్సిడీల గురించి అధికారిక సమాచారం ఎక్కడ లభిస్తుంది? అధికారిక వనరులను మాత్రమే పంచుకోండి.",
    },
]

DEMO_REPLIES = {
    "demo-post-irrigation": [
        {
            "author": "Demo farmer",
            "language": "te",
            "body": "డెమో సమాధానం: నేల తేమ పరిశీలించి, స్థానిక అనుభవం ఆధారంగా నిర్ణయం తీసుకోవాలి.",
        }
    ],
    "demo-post-weather": [
        {
            "author": "Demo farmer",
            "language": "en",
            "body": "Demo answer: many farmers look at the forecast and avoid spraying just before heavy rain. Confirm locally.",
        }
    ],
    "demo-post-crops": [],
    "demo-post-schemes": [],
}


def seed_demo_community() -> None:
    """Insert demo rows once, only when the community table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(CommunityPost.id).limit(1)).first()
        if existing:
            return

        for item in DEMO_POSTS:
            db.add(CommunityPost(**item, is_demo=True, status="published", reports=0))

        for post_id, replies in DEMO_REPLIES.items():
            for reply in replies:
                db.add(
                    CommunityReply(
                        id=uuid4().hex,
                        post_id=post_id,
                        **reply,
                        is_demo=True,
                        status="published",
                        reports=0,
                    )
                )

        db.commit()
