"""Administrator sign-in and moderation queues.

The browser uses an HttpOnly cookie plus a double-submit CSRF token. Bearer
tokens still work for API clients and automated tests. Moderation itself is
performed by the already-existing community status endpoints, now protected.
"""

import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select

from app.config import ADMIN_COOKIE_NAME, ADMIN_HINT_COOKIE_NAME, COOKIE_SECURE, CSRF_COOKIE_NAME
from app.db.connection import SessionLocal
from app.dependencies import require_admin, session_token_from_request
from app.models.community import CommunityPost, CommunityReply
from app.models.equipment import EquipmentEnquiry, EquipmentListing
from app.routers.community import media_for_posts
from app.routers.equipment import serialize_enquiry, serialize_listing
from app.schemas.admin import LoginIn
from app.schemas.equipment import AdminListingStatusIn
from app.services.auth import (
    LOGIN_LOCKOUT_SECONDS,
    TooManyLoginAttempts,
    authenticate,
    check_login_allowed,
    clear_failed_logins,
    create_session,
    delete_session,
    record_failed_login,
    SESSION_HOURS,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _serialize_post(row: CommunityPost, media=None) -> dict[str, Any]:
    return {
        "id": row.id,
        "author": row.author,
        "language": row.language,
        "category": row.category,
        "title": row.title,
        "body": row.body,
        "is_demo": row.is_demo,
        "status": row.status,
        "reports": row.reports,
        "media": (
            {"path": media.media_path, "kind": media.media_kind, "name": media.media_name}
            if media
            else None
        ),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_reply(row: CommunityReply) -> dict[str, Any]:
    return {
        "id": row.id,
        "post_id": row.post_id,
        "author": row.author,
        "language": row.language,
        "body": row.body,
        "is_demo": row.is_demo,
        "status": row.status,
        "reports": row.reports,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response) -> dict[str, Any]:
    """Public endpoint: verify credentials and set secure session cookies."""
    client_host = request.client.host if request.client else None

    try:
        check_login_allowed(payload.username, client_host)
    except TooManyLoginAttempts as exc:
        raise HTTPException(
            status_code=429,
            detail="Too many sign-in attempts. Please try again later.",
            headers={"Retry-After": str(LOGIN_LOCKOUT_SECONDS)},
        ) from exc

    admin = authenticate(payload.username, payload.password)
    if admin is None:
        record_failed_login(payload.username, client_host)
        # One generic message for both cases — do not reveal which name exists.
        raise HTTPException(status_code=401, detail="Invalid username or password")

    clear_failed_logins(payload.username, client_host)
    token, expires_at = create_session(admin.id)
    csrf_token = secrets.token_urlsafe(24)
    max_age = SESSION_HOURS * 60 * 60

    # JavaScript cannot read the session cookie. The readable CSRF cookie is
    # paired with the X-CSRF-Token header on every state-changing request.
    response.set_cookie(
        ADMIN_COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        ADMIN_HINT_COOKIE_NAME,
        "1",
        max_age=max_age,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    return {
        "username": admin.username,
        "expires_at": expires_at.isoformat(),
        "csrfToken": csrf_token,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    delete_session(session_token_from_request(request))
    response.delete_cookie(ADMIN_COOKIE_NAME, path="/", secure=COOKIE_SECURE, samesite="strict")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/", secure=COOKIE_SECURE, samesite="strict")
    response.delete_cookie(ADMIN_HINT_COOKIE_NAME, path="/", secure=COOKIE_SECURE, samesite="strict")
    return {"signed_out": True}


@router.get("/me")
def me(admin: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    return {"username": admin["username"]}


@router.get("/reports")
def reports(
    admin: dict[str, Any] = Depends(require_admin),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Farmer content that has been reported at least once."""
    with SessionLocal() as db:
        posts = db.execute(
            select(CommunityPost)
            .where(CommunityPost.reports > 0)
            .order_by(CommunityPost.reports.desc(), CommunityPost.created_at.desc())
            .limit(limit)
        ).scalars().all()
        replies = db.execute(
            select(CommunityReply)
            .where(CommunityReply.reports > 0)
            .order_by(CommunityReply.reports.desc(), CommunityReply.created_at.desc())
            .limit(limit)
        ).scalars().all()
        media = media_for_posts(db, [row.id for row in posts])
        return {
            "posts": [_serialize_post(row, media.get(row.id)) for row in posts],
            "replies": [_serialize_reply(row) for row in replies],
        }


@router.get("/queue")
def queue(
    admin: dict[str, Any] = Depends(require_admin),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Recent farmer-written content for review, including hidden items."""
    with SessionLocal() as db:
        posts = db.execute(
            select(CommunityPost)
            .where(CommunityPost.is_demo.is_(False))
            .order_by(CommunityPost.created_at.desc())
            .limit(limit)
        ).scalars().all()
        replies = db.execute(
            select(CommunityReply)
            .where(CommunityReply.is_demo.is_(False))
            .order_by(CommunityReply.created_at.desc())
            .limit(limit)
        ).scalars().all()
        media = media_for_posts(db, [row.id for row in posts])
        return {
            "posts": [_serialize_post(row, media.get(row.id)) for row in posts],
            "replies": [_serialize_reply(row) for row in replies],
        }


@router.get("/equipment/listings")
def equipment_listings(
    admin: dict[str, Any] = Depends(require_admin),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Owner-submitted equipment listings for administrator review."""
    with SessionLocal() as db:
        rows = db.execute(
            select(EquipmentListing)
            .where(EquipmentListing.is_demo.is_(False))
            .order_by(EquipmentListing.created_at.desc())
            .limit(limit)
        ).scalars().all()
        return {"listings": [serialize_listing(row, include_owner=True) for row in rows]}


@router.patch("/equipment/listings/{listing_id}")
def moderate_equipment_listing(
    listing_id: str,
    payload: AdminListingStatusIn,
    admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    """Hide an owner-submitted listing or restore it to the public list."""
    with SessionLocal() as db:
        row = db.get(EquipmentListing, listing_id)
        if row is None or row.is_demo:
            raise HTTPException(status_code=404, detail="Listing not found")

        row.status = payload.status
        db.commit()
        db.refresh(row)
        return serialize_listing(row, include_owner=True)


@router.get("/equipment/enquiries")
def equipment_enquiries(
    admin: dict[str, Any] = Depends(require_admin),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Rental enquiries for administrator oversight."""
    with SessionLocal() as db:
        pairs = db.execute(
            select(EquipmentEnquiry, EquipmentListing)
            .join(EquipmentListing, EquipmentEnquiry.listing_id == EquipmentListing.id)
            .order_by(EquipmentEnquiry.created_at.desc())
            .limit(limit)
        ).all()
        return {
            "enquiries": [
                serialize_enquiry(enquiry, listing, "admin") for enquiry, listing in pairs
            ]
        }
