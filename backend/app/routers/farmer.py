"""Farmer registration, sign-in and account-owned profile API.

Farmers get their own salted password hash, expiring session, HttpOnly cookie
and separate CSRF token. Their farm profile is stored under an id derived from
the account, so another farmer cannot read or overwrite it.
"""

import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..config import (
    COOKIE_SECURE,
    FARMER_COOKIE_NAME,
    FARMER_CSRF_COOKIE_NAME,
    FARMER_HINT_COOKIE_NAME,
)
from ..db.connection import SessionLocal
from ..dependencies import farmer_token_from_request, require_farmer
from ..models.profile import FarmerProfile
from ..routers.profile import save_record, serialize
from ..schemas.farmer import FarmerLoginIn, FarmerRegisterIn
from ..schemas.profile import ProfileIn
from ..services.farmer_auth import (
    LOGIN_LOCKOUT_SECONDS,
    SESSION_HOURS,
    TooManyLoginAttempts,
    authenticate,
    check_login_allowed,
    clear_failed_logins,
    create_farmer,
    create_session,
    delete_session,
    profile_id_for,
    record_failed_login,
)

router = APIRouter(prefix="/farmer", tags=["farmer"])


def _set_session_cookies(response: Response, token: str, csrf_token: str) -> None:
    max_age = SESSION_HOURS * 60 * 60
    response.set_cookie(
        FARMER_COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        FARMER_CSRF_COOKIE_NAME,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        FARMER_HINT_COOKIE_NAME,
        "1",
        max_age=max_age,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    for name in (FARMER_COOKIE_NAME, FARMER_CSRF_COOKIE_NAME, FARMER_HINT_COOKIE_NAME):
        response.delete_cookie(name, path="/", secure=COOKIE_SECURE, samesite="strict")


def _session_response(farmer: Any, response: Response, registered: bool = False) -> dict[str, Any]:
    token, expires_at = create_session(farmer.id)
    csrf_token = secrets.token_urlsafe(24)
    _set_session_cookies(response, token, csrf_token)
    return {
        "username": farmer.username,
        "display_name": farmer.display_name,
        "expires_at": expires_at.isoformat(),
        "csrfToken": csrf_token,
        "registered": registered,
    }


@router.post("/register")
def register(payload: FarmerRegisterIn, response: Response) -> dict[str, Any]:
    """Create a real farmer account and sign it in immediately."""
    try:
        farmer = create_farmer(payload.username, payload.password, payload.display_name)
    except ValueError as exc:
        status = 409 if "already exists" in str(exc) else 422
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return _session_response(farmer, response, registered=True)


@router.post("/login")
def login(payload: FarmerLoginIn, request: Request, response: Response) -> dict[str, Any]:
    client_host = request.client.host if request.client else None
    try:
        check_login_allowed(payload.username, client_host)
    except TooManyLoginAttempts as exc:
        raise HTTPException(
            status_code=429,
            detail="Too many sign-in attempts. Please try again later.",
            headers={"Retry-After": str(LOGIN_LOCKOUT_SECONDS)},
        ) from exc

    farmer = authenticate(payload.username, payload.password)
    if farmer is None:
        record_failed_login(payload.username, client_host)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    clear_failed_logins(payload.username, client_host)
    return _session_response(farmer, response)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    farmer: dict[str, Any] = Depends(require_farmer),
) -> dict[str, Any]:
    delete_session(farmer_token_from_request(request))
    _clear_session_cookies(response)
    return {"signed_out": True}


@router.get("/me")
def me(farmer: dict[str, Any] = Depends(require_farmer)) -> dict[str, Any]:
    return {
        "username": farmer["username"],
        "display_name": farmer["display_name"],
    }


@router.get("/profile")
def get_my_profile(farmer: dict[str, Any] = Depends(require_farmer)) -> dict[str, Any]:
    profile_id = profile_id_for(farmer["id"])
    with SessionLocal() as db:
        return serialize(db.get(FarmerProfile, profile_id), profile_id)


@router.put("/profile")
def save_my_profile(
    payload: ProfileIn,
    farmer: dict[str, Any] = Depends(require_farmer),
) -> dict[str, Any]:
    return save_record(profile_id_for(farmer["id"]), payload)
