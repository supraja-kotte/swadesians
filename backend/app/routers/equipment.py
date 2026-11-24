"""Owner-submitted equipment rental API, renter directory and enquiry flow.

Owners create and manage their own listings and renter profiles using a private
browser key. Farmers use another browser key to return to their enquiries.
Neither raw key is stored or returned by the API.
"""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import func, select

from ..db.connection import SessionLocal
from ..models.equipment import (
    EquipmentEnquiry,
    EquipmentListing,
    EquipmentProvider,
    EquipmentProviderEnquiry,
)
from ..schemas.equipment import (
    EnquiryIn,
    EnquiryUpdateIn,
    ListingIn,
    ListingUpdateIn,
    ProviderEnquiryIn,
    ProviderEnquiryUpdateIn,
    ProviderIn,
    VALID_EQUIPMENT_CATEGORIES,
)
from ..services.keys import hash_browser_key

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


def serialize_provider(
    row: EquipmentProvider,
    listings: list[EquipmentListing] | None = None,
    include_contact: bool = False,
) -> dict[str, Any]:
    """Return public renter fields; contact is opt-in only."""
    public_listings = listings or []
    result: dict[str, Any] = {
        "id": row.id,
        "display_name": row.display_name,
        "state": row.state,
        "district": row.district,
        "categories": [item for item in (row.categories or "").split(",") if item],
        "availability": row.availability,
        "description": row.description,
        "status": row.status,
        "is_demo": row.is_demo,
        "listing_count": len(public_listings),
        "listings": [serialize_listing(item) for item in public_listings],
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
    if include_contact:
        result["contact"] = row.contact
    return result


def serialize_provider_enquiry(
    row: EquipmentProviderEnquiry,
    provider: EquipmentProvider,
    audience: str,
) -> dict[str, Any]:
    """Return only the fields the requested audience is allowed to see."""
    result: dict[str, Any] = {
        "id": row.id,
        "provider_id": provider.id,
        "provider_name": provider.display_name,
        "status": row.status,
        "owner_reply": row.owner_reply,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
    if audience == "owner":
        result.update(
            {
                "farmer_name": row.name,
                "farmer_phone": row.phone,
                "message": row.message,
            }
        )
    if audience == "farmer":
        result["provider_contact"] = provider.contact
    return result


def _active_listings_for_owner(db, owner_key_hash: str) -> list[EquipmentListing]:
    return list(
        db.execute(
            select(EquipmentListing)
            .where(
                EquipmentListing.owner_key_hash == owner_key_hash,
                EquipmentListing.is_demo.is_(False),
                EquipmentListing.status == "active",
            )
            .order_by(EquipmentListing.created_at.desc())
        )
        .scalars()
        .all()
    )


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


@router.get("/providers")
def list_providers(
    category: str | None = Query(None, max_length=30),
    location: str | None = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Return active user-entered renters, with their public equipment summary."""
    with SessionLocal() as db:
        statement = (
            select(EquipmentProvider)
            .where(EquipmentProvider.is_demo.is_(False), EquipmentProvider.status == "active")
            .order_by(EquipmentProvider.created_at.desc())
        )

        if category and category != "all":
            _validate_category(category)
            statement = statement.where(EquipmentProvider.categories.like(f"%{category}%"))

        if location and location.strip():
            term = f"%{location.strip()}%"
            statement = statement.where(
                (EquipmentProvider.district.like(term)) | (EquipmentProvider.state.like(term))
            )

        rows = db.execute(statement.limit(limit)).scalars().all()
        return {
            "providers": [
                serialize_provider(row, _active_listings_for_owner(db, row.owner_key_hash))
                for row in rows
            ]
        }


@router.get("/providers/{provider_id}")
def get_provider(provider_id: str) -> dict[str, Any]:
    """Return one live renter profile with its current public equipment."""
    with SessionLocal() as db:
        row = db.get(EquipmentProvider, provider_id)
        if row is None or row.is_demo or row.status != "active":
            raise HTTPException(status_code=404, detail="Renter not available")
        return {
            "provider": serialize_provider(
                row, _active_listings_for_owner(db, row.owner_key_hash)
            )
        }


@router.put("/owner/provider")
def save_provider(
    payload: ProviderIn,
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Create or update this browser's renter profile."""
    data = payload.model_dump()
    owner_key_hash = hash_browser_key(owner_key)

    with SessionLocal() as db:
        row = db.scalar(
            select(EquipmentProvider).where(EquipmentProvider.owner_key_hash == owner_key_hash)
        )
        if row is None:
            row = EquipmentProvider(
                id=uuid4().hex,
                owner_key_hash=owner_key_hash,
                is_demo=False,
            )
            db.add(row)

        row.display_name = _clean(data["display_name"])
        row.contact = _clean(data["contact"])
        row.state = _clean(data["state"])
        row.district = _clean(data["district"])
        row.categories = ",".join(data["categories"])
        row.availability = _clean(data["availability"])
        row.description = _clean(data["description"])
        row.status = data["status"]

        db.commit()
        db.refresh(row)
        return serialize_provider(
            row, _active_listings_for_owner(db, row.owner_key_hash), include_contact=True
        )


@router.get("/owner/provider")
def get_own_provider(
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Return this browser's renter profile, if one has been created."""
    with SessionLocal() as db:
        row = db.scalar(
            select(EquipmentProvider).where(
                EquipmentProvider.owner_key_hash == hash_browser_key(owner_key)
            )
        )
        if row is None:
            return {"profile": None}
        return {
            "profile": serialize_provider(
                row, _active_listings_for_owner(db, row.owner_key_hash), include_contact=True
            )
        }


@router.post("/providers/{provider_id}/enquiries", status_code=201)
def create_provider_enquiry(provider_id: str, payload: ProviderEnquiryIn) -> dict[str, Any]:
    """Send a direct enquiry to a renter and return their submitted contact."""
    with SessionLocal() as db:
        provider = db.get(EquipmentProvider, provider_id)
        if provider is None or provider.is_demo or provider.status != "active":
            raise HTTPException(status_code=404, detail="Renter not available")

        row = EquipmentProviderEnquiry(
            id=uuid4().hex,
            provider_id=provider_id,
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
            "provider_id": provider_id,
            "provider_name": provider.display_name,
            "status": row.status,
            "provider_contact": provider.contact,
        }


@router.get("/owner/provider/enquiries")
def owner_provider_enquiries(
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Return direct enquiries sent to this browser's renter profile."""
    with SessionLocal() as db:
        provider = db.scalar(
            select(EquipmentProvider).where(
                EquipmentProvider.owner_key_hash == hash_browser_key(owner_key)
            )
        )
        if provider is None:
            return {"enquiries": []}

        rows = (
            db.execute(
                select(EquipmentProviderEnquiry)
                .where(EquipmentProviderEnquiry.provider_id == provider.id)
                .order_by(EquipmentProviderEnquiry.created_at.desc())
            )
            .scalars()
            .all()
        )
        return {
            "enquiries": [
                serialize_provider_enquiry(row, provider, "owner") for row in rows
            ]
        }


@router.patch("/owner/provider/enquiries/{enquiry_id}")
def update_provider_enquiry(
    enquiry_id: str,
    payload: ProviderEnquiryUpdateIn,
    owner_key: str = Header(..., alias="X-Owner-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Let a renter mark a direct enquiry contacted/closed and add a reply."""
    with SessionLocal() as db:
        enquiry = db.get(EquipmentProviderEnquiry, enquiry_id)
        if enquiry is None:
            raise HTTPException(status_code=404, detail="Enquiry not found")

        provider = db.get(EquipmentProvider, enquiry.provider_id)
        if provider is None or provider.owner_key_hash != hash_browser_key(owner_key):
            raise HTTPException(status_code=404, detail="Enquiry not found")

        enquiry.status = payload.status
        enquiry.owner_reply = payload.reply.strip()
        db.commit()
        db.refresh(enquiry)
        return serialize_provider_enquiry(enquiry, provider, "owner")


@router.get("/farmer/provider-enquiries")
def farmer_provider_enquiries(
    farmer_key: str = Header(..., alias="X-Farmer-Key", min_length=16, max_length=128),
) -> dict[str, Any]:
    """Return direct renter enquiries sent by this browser, with contacts."""
    with SessionLocal() as db:
        pairs = db.execute(
            select(EquipmentProviderEnquiry, EquipmentProvider)
            .join(EquipmentProvider, EquipmentProviderEnquiry.provider_id == EquipmentProvider.id)
            .where(EquipmentProviderEnquiry.farmer_key_hash == hash_browser_key(farmer_key))
            .order_by(EquipmentProviderEnquiry.created_at.desc())
        ).all()
        return {
            "enquiries": [
                serialize_provider_enquiry(enquiry, provider, "farmer")
                for enquiry, provider in pairs
            ]
        }
