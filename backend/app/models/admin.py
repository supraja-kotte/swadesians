"""Administrator accounts and short-lived sign-in sessions.

Passwords are stored only as a salted PBKDF2 hash. These accounts are for
moderators only; farmer accounts live in the separate farmer model.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func

from ..db.connection import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    token = Column(String, primary_key=True)
    admin_id = Column(String, ForeignKey("admins.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
