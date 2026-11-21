"""Smart farming guidance topics and farmer field notes.

Topics are neutral IDs; the translated explanations live in the frontend.
Field notes store what the farmer typed — there is no analysis or prediction.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.db.connection import Base


class SmartTopic(Base):
    __tablename__ = "smart_topics"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class SmartVideo(Base):
    """A verified external YouTube video. No title or claim is stored here."""

    __tablename__ = "smart_videos"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class FieldNote(Base):
    __tablename__ = "field_notes"

    id = Column(String, primary_key=True)
    field_name = Column(String(60), nullable=False)
    crop = Column(String(60), nullable=False)
    stage = Column(String(40), default="", nullable=False)
    observation = Column(String(500), default="", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
