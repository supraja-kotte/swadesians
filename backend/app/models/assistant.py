"""Neutral IDs for the voice assistant's fixed command list.

This module deliberately has no AI model, prediction or answer table. The
browser matches speech against a short translated keyword list; the backend
only supplies the neutral command IDs and categories for display.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.db.connection import Base


class VoiceCommand(Base):
    __tablename__ = "voice_commands"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
