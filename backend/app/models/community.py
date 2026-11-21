"""Community question-and-answer tables and their local media attachments."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.db.connection import Base


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(String, primary_key=True)
    author = Column(String(60), default="", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    category = Column(String(30), default="general", nullable=False)
    title = Column(String(140), nullable=False)
    body = Column(String(2000), nullable=False)
    # Demo rows are sample content and are clearly labelled in the UI.
    is_demo = Column(Boolean, default=False, nullable=False)
    # "published" or "hidden". Hidden rows are excluded from normal listings.
    status = Column(String(20), default="published", nullable=False)
    reports = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class CommunityMedia(Base):
    """One optional photo or video attached to a community post.

    A separate table keeps existing databases working: adding columns to
    community_posts would need an ALTER TABLE migration, while `create_all`
    creates this new table automatically.
    """

    __tablename__ = "community_media"

    id = Column(String, primary_key=True)
    post_id = Column(
        String,
        ForeignKey("community_posts.id"),
        nullable=False,
        index=True,
        unique=True,
    )
    # A same-origin URL such as /uploads/2026/11/<uuid>.jpg
    media_path = Column(String(500), nullable=False)
    # "image" or "video"
    media_kind = Column(String(10), nullable=False)
    # Sanitised original filename, shown in the UI only.
    media_name = Column(String(120), nullable=False, default="")
    created_at = Column(DateTime, server_default=func.now())


class CommunityReply(Base):
    __tablename__ = "community_replies"

    id = Column(String, primary_key=True)
    post_id = Column(String, ForeignKey("community_posts.id"), nullable=False, index=True)
    author = Column(String(60), default="", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    body = Column(String(1000), nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="published", nullable=False)
    reports = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
