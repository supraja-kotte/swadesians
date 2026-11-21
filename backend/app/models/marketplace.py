"""Marketplace demo produce listings and buyer enquiries."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.db.connection import Base


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(800), default="", nullable=False)
    state = Column(String(60), default="", nullable=False)
    district = Column(String(60), default="", nullable=False)
    market_hint = Column(String(120), default="", nullable=False)
    # No price is stored in demo data. Inventing rates would mislead farmers.
    price_amount = Column(Integer, nullable=True)
    price_unit = Column(String(20), nullable=True)
    quantity_label = Column(String(60), default="", nullable=False)
    is_demo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class MarketplaceEnquiry(Base):
    __tablename__ = "marketplace_enquiries"

    id = Column(String, primary_key=True)
    listing_id = Column(String, ForeignKey("marketplace_listings.id"), nullable=False, index=True)
    name = Column(String(60), nullable=False)
    phone = Column(String(20), nullable=False)
    quantity = Column(String(60), default="", nullable=False)
    message = Column(String(500), default="", nullable=False)
    status = Column(String(20), default="new", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
