"""Clearly labelled sample produce listings for the marketplace.

No real sellers, mandis, phone numbers or prices are included. Every row has
is_demo=True so the interface can show a visible warning. Live prices require a
verified data source and will be added only when one is available.
"""

from sqlalchemy import select

from app.db.connection import SessionLocal
from app.models.marketplace import MarketplaceListing

DEMO_LISTINGS = [
    ("grains", "Rice — sample listing", "Andhra Pradesh", "Guntur", "Sample local market", "1 quintal (sample)"),
    ("grains", "Maize — sample listing", "Telangana", "Warangal", "Sample local market", "1 quintal (sample)"),
    ("pulses", "Red gram — sample listing", "Telangana", "Mahbubnagar", "Sample local market", "1 quintal (sample)"),
    ("vegetables", "Tomato — sample listing", "Andhra Pradesh", "Vijayawada", "Sample local market", "1 bag (sample)"),
    ("vegetables", "Chilli — sample listing", "Andhra Pradesh", "Guntur", "Sample local market", "1 bag (sample)"),
    ("fruits", "Mango — sample listing", "Andhra Pradesh", "Tirupati", "Sample local market", "1 box (sample)"),
    ("oils", "Groundnut — sample listing", "Telangana", "Nalgonda", "Sample local market", "1 quintal (sample)"),
    ("spices", "Turmeric — sample listing", "Andhra Pradesh", "Anantapur", "Sample local market", "1 bag (sample)"),
]

DESCRIPTION = (
    "Demo listing only. This is sample content, not a real offer. No seller, "
    "contact detail, live price or market rate is provided."
)


def seed_demo_marketplace() -> None:
    """Insert sample rows once, only when the listing table is empty."""
    with SessionLocal() as db:
        existing = db.execute(select(MarketplaceListing.id).limit(1)).first()
        if existing:
            return

        for index, (category, title, state, district, market_hint, quantity) in enumerate(
            DEMO_LISTINGS, start=1
        ):
            db.add(
                MarketplaceListing(
                    id=f"demo-marketplace-{index}",
                    category=category,
                    title=title,
                    description=DESCRIPTION,
                    state=state,
                    district=district,
                    market_hint=market_hint,
                    price_amount=None,
                    price_unit=None,
                    quantity_label=quantity,
                    is_demo=True,
                )
            )

        db.commit()
