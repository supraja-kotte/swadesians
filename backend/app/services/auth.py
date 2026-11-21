"""Password hashing and session handling using only the Python standard library.

PBKDF2-HMAC-SHA256 with a random per-user salt is a real, salted password
hash — not plain text and not a reversible encoding. Session tokens are
random and expire, so a stolen token cannot be used forever.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import hashlib
import hmac
import secrets
import time

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.admin import Admin, AdminSession

PBKDF2_ITERATIONS = 200_000
SESSION_HOURS = 8

# A small in-process lockout against repeated guessing. A real deployment with
# several workers should use a shared store (Redis/database) instead.
MAX_FAILED_LOGINS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60
_failed_logins: dict[str, list[float]] = {}


class TooManyLoginAttempts(Exception):
    """Raised when a username has too many recent failed sign-in attempts."""


def _attempt_key(username: str, client_host: str | None) -> str:
    return f"{client_host or 'unknown'}|{username.strip().lower()}"


def _prune_expired(now: float) -> None:
    cutoff = now - LOGIN_LOCKOUT_SECONDS
    for key in list(_failed_logins):
        recent = [stamp for stamp in _failed_logins[key] if stamp >= cutoff]
        if recent:
            _failed_logins[key] = recent
        else:
            _failed_logins.pop(key, None)


def check_login_allowed(username: str, client_host: str | None) -> None:
    """Block a username after too many recent failures. Call before password check."""
    now = time.monotonic()
    _prune_expired(now)
    attempts = _failed_logins.get(_attempt_key(username, client_host), [])
    if len(attempts) >= MAX_FAILED_LOGINS:
        raise TooManyLoginAttempts


def record_failed_login(username: str, client_host: str | None) -> None:
    key = _attempt_key(username, client_host)
    _failed_logins.setdefault(key, []).append(time.monotonic())


def clear_failed_logins(username: str | None = None, client_host: str | None = None) -> None:
    """Forget failures after a successful login or in tests."""
    if username is None:
        _failed_logins.clear()
        return
    _failed_logins.pop(_attempt_key(username, client_host), None)


def _utc_now() -> datetime:
    """Naive UTC datetime, matching SQLAlchemy's SQLite DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Return (hex digest, hex salt)."""
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return digest.hex(), salt.hex()


def verify_password(password: str, password_hash: str, salt_hex: str) -> bool:
    candidate, _ = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, password_hash)


def create_admin(username: str, password: str) -> Admin:
    """Create one administrator. Raises ValueError if the name is taken."""
    name = username.strip()
    if len(name) < 3 or len(password) < 12:
        raise ValueError("Username must be 3+ characters and password 12+ characters")

    password_hash, salt = hash_password(password)
    with SessionLocal() as db:
        if db.execute(select(Admin.id).where(Admin.username == name)).first():
            raise ValueError("That username already exists")

        admin = Admin(
            id=uuid4().hex,
            username=name,
            password_hash=password_hash,
            salt=salt,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin


def authenticate(username: str, password: str) -> Admin | None:
    """Return the admin when credentials are valid, otherwise None."""
    with SessionLocal() as db:
        admin = db.execute(
            select(Admin).where(Admin.username == username.strip())
        ).scalar_one_or_none()
        if admin is None or not admin.is_active:
            return None
        if not verify_password(password, admin.password_hash, admin.salt):
            return None
        return admin


def create_session(admin_id: str) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = _utc_now() + timedelta(hours=SESSION_HOURS)
    with SessionLocal() as db:
        db.add(AdminSession(token=token, admin_id=admin_id, expires_at=expires_at))
        db.commit()
    return token, expires_at


def get_admin_by_token(token: str) -> dict[str, Any] | None:
    """Resolve a live session token to its admin, or None if invalid/expired."""
    if not token:
        return None
    with SessionLocal() as db:
        row = db.execute(
            select(Admin, AdminSession).join(
                AdminSession, AdminSession.admin_id == Admin.id
            ).where(AdminSession.token == token)
        ).one_or_none()
        if row is None:
            return None
        admin, session = row
        if not admin.is_active or session.expires_at <= _utc_now():
            return None
        return {"id": admin.id, "username": admin.username}


def delete_session(token: str) -> None:
    with SessionLocal() as db:
        session = db.get(AdminSession, token)
        if session is not None:
            db.delete(session)
            db.commit()
