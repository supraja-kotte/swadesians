"""Reusable administrator access control and CSRF protection."""

import secrets
from typing import Any

from fastapi import HTTPException, Request

from app.config import ADMIN_COOKIE_NAME, CSRF_COOKIE_NAME
from app.services.auth import get_admin_by_token

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _deny() -> None:
    raise HTTPException(
        status_code=401,
        detail="Administrator sign-in required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def session_token_from_request(request: Request) -> str:
    """An explicit Bearer token wins; otherwise use the HttpOnly cookie."""
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization[7:].strip()
    return request.cookies.get(ADMIN_COOKIE_NAME, "")


def uses_cookie_auth(request: Request) -> bool:
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return False
    return bool(request.cookies.get(ADMIN_COOKIE_NAME))


def validate_csrf(request: Request) -> None:
    """Double-submit check for cookie-authenticated state changes."""
    cookie_value = request.cookies.get(CSRF_COOKIE_NAME, "")
    header_value = request.headers.get("X-CSRF-Token", "")
    if not cookie_value or not header_value or not secrets.compare_digest(cookie_value, header_value):
        raise HTTPException(status_code=403, detail="CSRF check failed")


def require_admin(request: Request) -> dict[str, Any]:
    """FastAPI dependency: reject the request unless a live admin session exists."""
    token = session_token_from_request(request)
    admin = get_admin_by_token(token)
    if admin is None:
        _deny()

    if uses_cookie_auth(request) and request.method in MUTATING_METHODS:
        validate_csrf(request)

    return admin


def require_admin_value(request: Request) -> dict[str, Any]:
    """Same check for endpoints that only sometimes need admin rights."""
    return require_admin(request)
