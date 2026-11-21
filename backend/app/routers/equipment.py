"""Equipment listing API (demo data) and enquiry flow."""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.equipment import EquipmentEnquiry, EquipmentListing
from app.schemas.equipment import EnquiryIn, VALID_EQUIPMENT_CATEGORIES

router = APIRouter(prefix="/equipment", tags=["equipment"])


def serialize_listing(row: EquipmentListing) -> dict[str, Any]:
    return {
        "id": row.id,
        "category": row.category,
        "title": row.title,
        "description": row.description,
        "state": row.state,
        "district": row.district,
        "price_amount": row.price_amount,
        "price_unit": row.price_unit,
        "owner_label": row.owner_label,
        "is_demo": row.is_demo,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/listings")
def list_listings(
    category: str | None = Query(None, max_length=30),
    location: str | None = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Return demo listings, optionally filtered by category and place name."""
    with SessionLocal() as db:
        statement = select(EquipmentListing).order_by(EquipmentListing.created_at.desc())

        if category and category != "all":
            if category not in VALID_EQUIPMENT_CATEGORIES:
                raise HTTPException(status_code=422, detail="Unknown category")
            statement = statement.where(EquipmentListing.category == category)

        if location and location.strip():
            term = f"%{location.strip()}%"
            statement = statement.where(
                (EquipmentListing.district.like(term)) | (EquipmentListing.state.like(term))
            )

        rows = db.execute(statement.limit(limit)).scalars().all()
        return {"listings": [serialize_listing(row) for row in rows]}


@router.post("/listings/{listing_id}/enquiries", status_code=201)
def create_enquiry(listing_id: str, payload: EnquiryIn) -> dict[str, Any]:
    """Save a rental enquiry.

    The listing is demo data, so the response says clearly that nobody will be
    contacted. The saved enquiry is for the future verified-provider workflow.
    """
    with SessionLocal() as db:
        listing = db.get(EquipmentListing, listing_id)
        if listing is None:
            raise HTTPException(status_code=404, detail="Listing not found")

        row = EquipmentEnquiry(
            id=uuid4().hex,
            listing_id=listing_id,
            name=payload.name.strip(),
            phone=payload.phone.strip(),
            message=payload.message.strip(),
            status="new",
        )
        db.add(row)
        db.commit()

        return {
            "id": row.id,
            "listing_id": listing_id,
            "status": row.status,
            "is_demo": True,
            "note": "Demo enquiry saved. No real provider will contact you.",
        }
