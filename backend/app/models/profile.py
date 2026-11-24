"""Farmer profile table.

Signed-in farmers own a profile id derived from their account. Anonymous
visitors may still use a browser-generated id, but the account-owned route is
the supported way to save a private profile.
"""

from sqlalchemy import Column, DateTime, String, func

from ..db.connection import Base


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(String, primary_key=True)
    state = Column(String(60), default="", nullable=False)
    district = Column(String(60), default="", nullable=False)
    crop = Column(String(40), default="", nullable=False)
    land_size = Column(String(20), default="", nullable=False)
    soil_type = Column(String(40), default="", nullable=False)
    irrigation = Column(String(40), default="", nullable=False)
    # SQLite stores the interest list as a simple comma-separated string.
    interests = Column(String(200), default="", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
