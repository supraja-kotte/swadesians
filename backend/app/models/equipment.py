"""Equipment rental demo listings and enquiries."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.db.connection import Base


class EquipmentListing(Base):
    __tablename__ = "equipment_listings"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(800), default="", nullable=False)
    state = Column(String(60), default="", nullable=False)
    district = Column(String(60), default="", nullable=False)
    # Price fields are intentionally empty in demo data. A real price is never
    # invented — later phases can fill these from verified providers.
    price_amount = Column(Integer, nullable=True)
    price_unit = Column(String(20), nullable=True)
    owner_label = Column(String(60), default="Demo owner", nullable=False)
    is_demo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class EquipmentEnquiry(Base):
    __tablename__ = "equipment_enquiries"

    id = Column(String, primary_key=True)
    listing_id = Column(String, ForeignKey("equipment_listings.id"), nullable=False, index=True)
    name = Column(String(60), nullable=False)
    phone = Column(String(20), nullable=False)
    message = Column(String(500), default="", nullable=False)
    status = Column(String(20), default="new", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
