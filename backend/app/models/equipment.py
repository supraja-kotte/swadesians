"""Owner-submitted equipment listings and rental enquiries.

A listing is created by the person who says they own the equipment. AgriGuide
does not invent an owner, contact detail, price or availability. The raw
browser keys are never stored: only their SHA-256 hashes, which let owners and
farmers return to their own records without a public account system.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.db.connection import Base


class EquipmentListing(Base):
    __tablename__ = "equipment_listings"

    id = Column(String, primary_key=True)
    category = Column(String(30), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(800), default="", nullable=False)
    state = Column(String(60), nullable=False)
    district = Column(String(60), nullable=False)
    price_amount = Column(Integer, nullable=True)
    price_unit = Column(String(20), nullable=True)
    owner_label = Column(String(60), nullable=False)
    owner_contact = Column(String(120), default="", nullable=False)
    owner_key_hash = Column(String(64), default="", nullable=False, index=True)
    availability = Column(String(120), default="", nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class EquipmentEnquiry(Base):
    __tablename__ = "equipment_enquiries"

    id = Column(String, primary_key=True)
    listing_id = Column(String, ForeignKey("equipment_listings.id"), nullable=False, index=True)
    name = Column(String(60), nullable=False)
    phone = Column(String(20), nullable=False)
    message = Column(String(500), default="", nullable=False)
    farmer_key_hash = Column(String(64), default="", nullable=False, index=True)
    status = Column(String(20), default="new", nullable=False)
    owner_reply = Column(String(300), default="", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
