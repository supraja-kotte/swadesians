"""Farmer accounts and short-lived sign-in sessions.

Farmer accounts are separate from administrator accounts. Passwords are stored
only as salted PBKDF2 hashes, never as plain text.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func

from ..db.connection import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String, primary_key=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    display_name = Column(String(60), default="", nullable=False)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class FarmerSession(Base):
    __tablename__ = "farmer_sessions"

    token = Column(String, primary_key=True)
    farmer_id = Column(String, ForeignKey("farmers.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
