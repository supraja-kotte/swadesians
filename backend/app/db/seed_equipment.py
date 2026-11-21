"""Clearly labelled sample equipment listings.

No real sellers, businesses, phone numbers or prices are included. Every row
has is_demo=True so the interface can show a visible warning. Real listings
will be added only from verified sources in a later phase.
"""

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.equipment import EquipmentListing

DEMO_LISTINGS = [
    ("tractors", "Tractor — sample listing", "Andhra Pradesh", "Guntur"),
    ("tillage", "Rotavator — sample listing", "Telangana", "Warangal"),
    ("harvesting", "Harvester — sample listing", "Andhra Pradesh", "Vijayawada"),
    ("irrigation", "Pump set — sample listing", "Telangana", "Hyderabad"),
    ("spraying", "Sprayer — sample listing", "Andhra Pradesh", "Tirupati"),
    ("transport", "Trailer — sample listing", "Telangana", "Nalgonda"),
    ("other", "Seed drill — sample listing", "Andhra Pradesh", "Anantapur"),
]

DESCRIPTION = (
    "Demo listing only. This is sample content, not a real offer. "
    "No owner, contact detail or price is provided."
)


def seed_demo_equipment() -> None:
    """Insert sample rows once, only when the listing table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(EquipmentListing.id).limit(1)).first()
        if existing:
            return

        for index, (category, title, state, district) in enumerate(DEMO_LISTINGS, start=1):
            db.add(
                EquipmentListing(
                    id=f"demo-equipment-{index}",
                    category=category,
                    title=title,
                    description=DESCRIPTION,
                    state=state,
                    district=district,
                    price_amount=None,
                    price_unit=None,
                    owner_label="Demo owner",
                    is_demo=True,
                )
            )

        db.commit()
