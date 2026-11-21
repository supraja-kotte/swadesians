"""Government scheme guidance topics, verified links and personal questions.

Guidance topics stay as neutral IDs with translated explanations in the
frontend. Verified links store a proper-noun scheme name and an official URL,
but deliberately no benefit amounts, eligibility rules or application claims.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.db.connection import Base


class SchemeTopic(Base):
    __tablename__ = "scheme_topics"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class SchemeQuestion(Base):
    __tablename__ = "scheme_questions"

    id = Column(String, primary_key=True)
    question = Column(String(300), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class SchemeLink(Base):
    """An officially verified government URL, grouped as central or state."""

    __tablename__ = "scheme_links"

    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False)
    level = Column(String(20), nullable=False, index=True)
    state = Column(String(40), nullable=True, index=True)
    url = Column(String(500), nullable=False)
    source_domain = Column(String(120), nullable=False)
    verified_on = Column(String(10), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
