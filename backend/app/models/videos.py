"""Demo video entries and a local save list.

No video files, links or channels are stored. Entries are neutral IDs whose
translated titles and summaries live in the frontend.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.db.connection import Base


class VideoEntry(Base):
    __tablename__ = "video_entries"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_demo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class SavedVideo(Base):
    __tablename__ = "saved_videos"

    video_id = Column(String, ForeignKey("video_entries.id"), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
