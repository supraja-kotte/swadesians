"""Marketplace API (demo produce listings) and buyer enquiry flow."""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.marketplace import MarketplaceEnquiry, MarketplaceListing
from app.schemas.marketplace import EnquiryIn, VALID_MARKETPLACE_CATEGORIES

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def serialize_listing(row: MarketplaceListing) -> dict[str, Any]:
    return {
        "id": row.id,
        "category": row.category,
        "title": row.title,
        "description": row.description,
        "state": row.state,
        "district": row.district,
        "market_hint": row.market_hint,
        "price_amount": row.price_amount,
        "price_unit": row.price_unit,
        "quantity_label": row.quantity_label,
        "is_demo": row.is_demo,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/listings")
def list_listings(
    category: str | None = Query(None, max_length=30),
    location: str | None = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Return demo produce listings, optionally filtered by category and place."""
    with SessionLocal() as db:
        statement = select(MarketplaceListing).order_by(MarketplaceListing.created_at.desc())

        if category and category != "all":
            if category not in VALID_MARKETPLACE_CATEGORIES:
                raise HTTPException(status_code=422, detail="Unknown category")
            statement = statement.where(MarketplaceListing.category == category)

        if location and location.strip():
            term = f"%{location.strip()}%"
            statement = statement.where(
                (MarketplaceListing.district.like(term)) | (MarketplaceListing.state.like(term))
            )

        rows = db.execute(statement.limit(limit)).scalars().all()
        return {"listings": [serialize_listing(row) for row in rows]}


@router.post("/listings/{listing_id}/enquiries", status_code=201)
def create_enquiry(listing_id: str, payload: EnquiryIn) -> dict[str, Any]:
    """Save a buyer enquiry against a demo listing.

    The response says clearly that this is demo content and no seller will be
    contacted. The record is useful for a later verified-seller workflow.
    """
    with SessionLocal() as db:
        listing = db.get(MarketplaceListing, listing_id)
        if listing is None:
            raise HTTPException(status_code=404, detail="Listing not found")

        row = MarketplaceEnquiry(
            id=uuid4().hex,
            listing_id=listing_id,
            name=payload.name.strip(),
            phone=payload.phone.strip(),
            quantity=payload.quantity.strip(),
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
            "note": "Demo enquiry saved. No real seller will contact you.",
        }
