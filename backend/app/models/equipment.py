"""Owner-submitted equipment listings, renter profiles and rental enquiries.

A listing or renter profile is created by the person who says they have the
equipment. AgriGuide does not invent a renter, contact detail, price or
availability. The raw browser keys are never stored: only their SHA-256 hashes,
which let providers and farmers return to their own records without a public
account system.
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


class EquipmentProvider(Base):
    """A user-entered renter who can be found by farmers directly."""

    __tablename__ = "equipment_providers"

    id = Column(String, primary_key=True)
    owner_key_hash = Column(String(64), default="", nullable=False, index=True)
    display_name = Column(String(60), nullable=False)
    contact = Column(String(120), nullable=False)
    state = Column(String(60), nullable=False)
    district = Column(String(60), nullable=False)
    categories = Column(String(200), default="", nullable=False)
    availability = Column(String(120), default="", nullable=False)
    description = Column(String(500), default="", nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EquipmentProviderEnquiry(Base):
    """A direct farmer-to-renter enquiry, separate from equipment listings."""

    __tablename__ = "equipment_provider_enquiries"

    id = Column(String, primary_key=True)
    provider_id = Column(
        String, ForeignKey("equipment_providers.id"), nullable=False, index=True
    )
    name = Column(String(60), nullable=False)
    phone = Column(String(20), nullable=False)
    message = Column(String(500), default="", nullable=False)
    farmer_key_hash = Column(String(64), default="", nullable=False, index=True)
    status = Column(String(20), default="new", nullable=False)
    owner_reply = Column(String(300), default="", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
