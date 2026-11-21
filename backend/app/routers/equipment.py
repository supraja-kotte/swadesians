"""Owner-submitted equipment rental API and enquiry workflow.

Owners create and manage their own listings using a private browser key.
Farmers use another browser key to return to their enquiries. Neither raw key
is stored or returned by the API.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import func, select

from app.db.connection import SessionLocal
from app.models.equipment import EquipmentEnquiry, EquipmentListing
from app.schemas.equipment import (
    EnquiryIn,
    EnquiryUpdateIn,
    ListingIn,
    ListingUpdateIn,
    VALID_EQUIPMENT_CATEGORIES,
)
from app.services.keys import hash_browser_key

router = APIRouter(prefix="/equipment", tags=["equipment"])


def _clean(value: str) -> str:
    return value.strip()


def serialize_listing(row: EquipmentListing, include_owner: bool = False) -> dict[str, Any]:
    """Return public listing fields; owner contact is opt-in only."""
    result: dict[str, Any] = {
        "id": row.id,
        "category": row.category,
        "title": row.title,
        "description": row.description,
        "state": row.state,
        "district": row.district,
        "price_amount": row.price_amount,
        "price_unit": row.price_unit,
        "owner_label": row.owner_label,
        "availability": row.availability,
        "status": row.status,
        "is_demo": row.is_demo,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
    if include_owner:
        result["owner_contact"] = row.owner_contact
    return result


def serialize_enquiry(
    row: EquipmentEnquiry,
    listing: EquipmentListing,
    audience: str,
) -> dict[str, Any]:
    """Return only the fields the requested audience is allowed to see."""
    result: dict[str, Any] = {
        "id": row.id,
        "listing_id": listing.id,
        "listing_title": listing.title,
        "listing_category": listing.category,
        "status": row.status,
        "owner_reply": row.owner_reply,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }

    if audience in {"owner", "admin"}:
        result.update(
            {
                "farmer_name": row.name,
                "farmer_phone": row.phone,
                "message": row.message,
            }
        )

    if audience in {"farmer", "admin"}:
        result.update(
            {
                "owner_label": listing.owner_label,
                "owner_contact": listing.owner_contact,
            }
        )

    return result


def _validate_category(value: str) -> None:
    if value not in VALID_EQUIPMENT_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown category")


@router.get("/listings")
def list_listings(
    category: str | None = Query(None, max_length=30),
    location: str | None = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Return active owner-submitted listings, filtered by category or place."""
    with SessionLocal() as db:
        statement = (
            select(EquipmentListing)
            .where(EquipmentListing.is_demo.is_(False), EquipmentListing.status == "active")
            .order_by(EquipmentListing.created_at.desc())
        )

        if category and category != "all":
            _validate_category(category)
            statement = statement.where(EquipmentListing.category == category)

        if location and location.strip():
            term = f"%{location.strip()}%"
            statement = statement.where(
                (EquipmentListing.district.like(term)) | (EquipmentListing.state.like(term))
            )

        rows = db.execute(statement.limit(limit)).scalars().all()
        return {"listings": [serialize_listing(row) for row in rows]}


@router.post("/listings", status_code=201)
def create_listing(payload: ListingIn) -> dict[str, Any]:
    """Publish a listing supplied by its owner."""
    data = payload.model_dump()
    owner_key = data.pop("owner_key")

    row = EquipmentListing(
        id=uuid4().hex,
        category=data["category"],
        title=_clean(data["title"]),
        description=_clean(data["description"]),
        state=_clean(data["state"]),
        district=_clean(data["district"]),
        price_amount=data["price_amount"],
        price_unit=data["price_unit"],
        owner_label=_clean(data["owner_label"]),
        owner_contact=_clean(data["owner_contact"]),
        owner_key_hash=hash_browser_key(owner_key),
        availability=_clean(data["availability"]),
        status="active",
        is_demo=False,
    )

    with SessionLocal() as db:
        db.add(row)
        db.commit()
        db.refresh(row)
        return serialize_listing(row, include_owner=True)


@router.get("/owner/listings")
def owner_listings(
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Return every listing belonging to this browser's owner key."""
    with SessionLocal() as db:
        rows = db.execute(
            select(EquipmentListing)
            .where(EquipmentListing.owner_key_hash == hash_browser_key(owner_key))
            .order_by(EquipmentListing.created_at.desc())
        ).scalars().all()

        result = []
        for row in rows:
            new_count = db.scalar(
                select(func.count(EquipmentEnquiry.id)).where(
                    EquipmentEnquiry.listing_id == row.id,
                    EquipmentEnquiry.status == "new",
                )
            )
            result.append({**serialize_listing(row, include_owner=True), "new_enquiries": new_count or 0})
        return {"listings": result}


@router.patch("/owner/listings/{listing_id}")
def update_own_listing(
    listing_id: str,
    payload: ListingUpdateIn,
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Edit an owner's own listing or pause/resume it."""
    values = payload.model_dump(exclude_unset=True)

    with SessionLocal() as db:
        row = db.get(EquipmentListing, listing_id)
        if row is None or row.is_demo or row.owner_key_hash != hash_browser_key(owner_key):
            raise HTTPException(status_code=404, detail="Listing not found")

        if row.status == "hidden":
            raise HTTPException(status_code=403, detail="Listing hidden by moderator")

        for field, value in values.items():
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
            setattr(row, field, value)

        db.commit()
        db.refresh(row)
        return serialize_listing(row, include_owner=True)


@router.get("/owner/enquiries")
def owner_enquiries(
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Return rental enquiries sent to this owner's listings."""
    with SessionLocal() as db:
        pairs = db.execute(
            select(EquipmentEnquiry, EquipmentListing)
            .join(EquipmentListing, EquipmentEnquiry.listing_id == EquipmentListing.id)
            .where(EquipmentListing.owner_key_hash == hash_browser_key(owner_key))
            .order_by(EquipmentEnquiry.created_at.desc())
        ).all()
        return {
            "enquiries": [
                serialize_enquiry(enquiry, listing, "owner") for enquiry, listing in pairs
            ]
        }


@router.patch("/owner/enquiries/{enquiry_id}")
def update_enquiry(
    enquiry_id: str,
    payload: EnquiryUpdateIn,
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Let an owner mark an enquiry contacted/closed and add a short reply."""
    with SessionLocal() as db:
        enquiry = db.get(EquipmentEnquiry, enquiry_id)
        if enquiry is None:
            raise HTTPException(status_code=404, detail="Enquiry not found")

        listing = db.get(EquipmentListing, enquiry.listing_id)
        if listing is None or listing.owner_key_hash != hash_browser_key(owner_key):
            raise HTTPException(status_code=404, detail="Enquiry not found")

        enquiry.status = payload.status
        enquiry.owner_reply = payload.reply.strip()
        db.commit()
        db.refresh(enquiry)
        return serialize_enquiry(enquiry, listing, "owner")


@router.get("/farmer/enquiries")
def farmer_enquiries(
    farmer_key: str = Header(..., alias="X-Farmer-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Return enquiries sent by this browser, including the owner's contact."""
    with SessionLocal() as db:
        pairs = db.execute(
            select(EquipmentEnquiry, EquipmentListing)
            .join(EquipmentListing, EquipmentEnquiry.listing_id == EquipmentListing.id)
            .where(EquipmentEnquiry.farmer_key_hash == hash_browser_key(farmer_key))
            .order_by(EquipmentEnquiry.created_at.desc())
        ).all()
        return {
            "enquiries": [
                serialize_enquiry(enquiry, listing, "farmer") for enquiry, listing in pairs
            ]
        }


@router.post("/listings/{listing_id}/enquiries", status_code=201)
def create_enquiry(listing_id: str, payload: EnquiryIn) -> dict[str, Any]:
    """Send a rental enquiry and return the owner's submitted contact detail."""
    with SessionLocal() as db:
        listing = db.get(EquipmentListing, listing_id)
        if listing is None or listing.is_demo or listing.status != "active":
            raise HTTPException(status_code=404, detail="Listing not available")

        row = EquipmentEnquiry(
            id=uuid4().hex,
            listing_id=listing_id,
            name=_clean(payload.name),
            phone=_clean(payload.phone),
            message=_clean(payload.message),
            farmer_key_hash=hash_browser_key(payload.farmer_key),
            status="new",
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return {
            "id": row.id,
            "listing_id": listing_id,
            "listing_title": listing.title,
            "status": row.status,
            "owner_label": listing.owner_label,
            "owner_contact": listing.owner_contact,
        }
