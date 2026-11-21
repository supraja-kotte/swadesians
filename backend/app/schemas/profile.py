"""Validation rules for profile requests."""

from pydantic import BaseModel, Field


class ProfileIn(BaseModel):
    state: str = Field("", max_length=60)
    district: str = Field("", max_length=60)
    crop: str = Field("", max_length=40)
    land_size: str = Field("", max_length=20)
    soil_type: str = Field("", max_length=40)
    irrigation: str = Field("", max_length=40)
    interests: list[str] = Field(default_factory=list, max_length=12)
