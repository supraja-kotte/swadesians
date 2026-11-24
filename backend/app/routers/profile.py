"""Farmer profile API.

The profile is optional. An empty profile is returned for an unknown ID so the
dashboard can work without personalisation.
"""

from typing import Any

from fastapi import APIRouter

from ..db.connection import SessionLocal
from ..models.profile import FarmerProfile
from ..schemas.profile import ProfileIn

router = APIRouter(prefix="/profile", tags=["profile"])

FIELDS = ("state", "district", "crop", "land_size", "soil_type", "irrigation")


def serialize(row: FarmerProfile | None, profile_id: str) -> dict[str, Any]:
    if row is None:
        return {
            "id": profile_id,
            "state": "",
            "district": "",
            "crop": "",
            "land_size": "",
            "soil_type": "",
            "irrigation": "",
            "interests": [],
            "updated_at": None,
        }

    return {
        "id": row.id,
        **{field: getattr(row, field) for field in FIELDS},
        "interests": [item for item in row.interests.split(",") if item],
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("/{profile_id}")
def get_profile(profile_id: str) -> dict[str, Any]:
    with SessionLocal() as db:
        return serialize(db.get(FarmerProfile, profile_id), profile_id)


def save_record(profile_id: str, payload: ProfileIn) -> dict[str, Any]:
    """Upsert one profile record. Callers decide who is allowed to use it."""
    with SessionLocal() as db:
        row = db.get(FarmerProfile, profile_id)
        if row is None:
            row = FarmerProfile(id=profile_id)
            db.add(row)

        for field in FIELDS:
            setattr(row, field, getattr(payload, field))
        row.interests = ",".join(payload.interests)

        db.commit()
        db.refresh(row)
        return serialize(row, profile_id)


@router.put("/{profile_id}")
def save_profile(profile_id: str, payload: ProfileIn) -> dict[str, Any]:
    return save_record(profile_id, payload)
