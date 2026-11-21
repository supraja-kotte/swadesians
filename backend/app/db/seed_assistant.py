"""Neutral command IDs for the demo voice assistant.

No phrase text is stored here. Spoken keywords and their translations live in
the frontend i18n file, so adding a language never requires a database change.
"""

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.assistant import VoiceCommand

DEMO_COMMANDS = [
    ("navigation", "nav-home"),
    ("navigation", "nav-weather"),
    ("navigation", "nav-schemes"),
    ("navigation", "nav-community"),
    ("navigation", "nav-videos"),
    ("navigation", "nav-marketplace"),
    ("navigation", "nav-equipment"),
    ("navigation", "nav-smart"),
    ("navigation", "nav-dashboard"),
    ("reading", "read-page"),
    ("reading", "stop-reading"),
    ("help", "help"),
]


def seed_demo_commands() -> None:
    """Insert command rows once, only when the table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(VoiceCommand.id).limit(1)).first()
        if existing:
            return

        for order, (category, command_id) in enumerate(DEMO_COMMANDS, start=1):
            db.add(
                VoiceCommand(
                    id=command_id,
                    category=category,
                    sort_order=order,
                    is_demo=True,
                )
            )

        db.commit()
