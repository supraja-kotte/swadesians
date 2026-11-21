"""Farmer account creation, authentication and session handling.

This mirrors the administrator auth service but uses its own tables, cookies
and lockout state. Password hashing is the same salted PBKDF2 implementation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import secrets
import time

from sqlalchemy import func, select

from app.db.connection import SessionLocal
from app.models.farmer import Farmer, FarmerSession
from app.services.auth import SESSION_HOURS, hash_password, verify_password

MAX_FAILED_LOGINS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60
_failed_logins: dict[str, list[float]] = {}


class TooManyLoginAttempts(Exception):
    """Raised when a farmer username has too many recent failed attempts."""


def _attempt_key(username: str, client_host: str | None) -> str:
    return f"{client_host or 'unknown'}|farmer|{username.strip().lower()}"


def _prune_expired(now: float) -> None:
    cutoff = now - LOGIN_LOCKOUT_SECONDS
    for key in list(_failed_logins):
        recent = [stamp for stamp in _failed_logins[key] if stamp >= cutoff]
        if recent:
            _failed_logins[key] = recent
        else:
            _failed_logins.pop(key, None)


def check_login_allowed(username: str, client_host: str | None) -> None:
    now = time.monotonic()
    _prune_expired(now)
    if len(_failed_logins.get(_attempt_key(username, client_host), [])) >= MAX_FAILED_LOGINS:
        raise TooManyLoginAttempts


def record_failed_login(username: str, client_host: str | None) -> None:
    _failed_logins.setdefault(_attempt_key(username, client_host), []).append(time.monotonic())


def clear_failed_logins(username: str | None = None, client_host: str | None = None) -> None:
    if username is None:
        _failed_logins.clear()
        return
    _failed_logins.pop(_attempt_key(username, client_host), None)


def _utc_now() -> datetime:
    """Naive UTC datetime, matching SQLAlchemy's SQLite DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_farmer(username: str, password: str, display_name: str = "") -> Farmer:
    """Create a farmer account. Raises ValueError for invalid or duplicate names."""
    name = username.strip()
    if len(name) < 3 or len(name) > 80:
        raise ValueError("Username must be 3-80 characters")
    if len(password) < 8 or len(password) > 200:
        raise ValueError("Password must be 8-200 characters")

    password_hash, salt = hash_password(password)
    label = display_name.strip() or name
    with SessionLocal() as db:
        existing = db.execute(
            select(Farmer.id).where(func.lower(Farmer.username) == name.lower())
        ).first()
        if existing:
            raise ValueError("That username already exists")

        farmer = Farmer(
            id=uuid4().hex,
            username=name,
            display_name=label[:60],
            password_hash=password_hash,
            salt=salt,
            is_active=True,
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
        return farmer


def authenticate(username: str, password: str) -> Farmer | None:
    with SessionLocal() as db:
        farmer = db.execute(
            select(Farmer).where(func.lower(Farmer.username) == username.strip().lower())
        ).scalar_one_or_none()
        if farmer is None or not farmer.is_active:
            return None
        if not verify_password(password, farmer.password_hash, farmer.salt):
            return None
        return farmer


def create_session(farmer_id: str) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + timedelta(hours=SESSION_HOURS)
    with SessionLocal() as db:
        db.add(FarmerSession(token=token, farmer_id=farmer_id, expires_at=expires_at))
        db.commit()
    return token, expires_at


def get_farmer_by_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    with SessionLocal() as db:
        row = db.execute(
            select(Farmer, FarmerSession).join(
                FarmerSession, FarmerSession.farmer_id == Farmer.id
            ).where(FarmerSession.token == token)
        ).one_or_none()
        if row is None:
            return None
        farmer, session = row
        if not farmer.is_active or session.expires_at <= _utc_now():
            return None
        return {"id": farmer.id, "username": farmer.username, "display_name": farmer.display_name}


def delete_session(token: str) -> None:
    with SessionLocal() as db:
        session = db.get(FarmerSession, token)
        if session is not None:
            db.delete(session)
            db.commit()


def profile_id_for(farmer_id: str) -> str:
    """A deterministic, account-owned profile id that cannot collide with browser ids."""
    return f"farmer-{farmer_id}"
