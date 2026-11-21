"""Validation rules for equipment enquiries."""

from pydantic import BaseModel, Field

VALID_EQUIPMENT_CATEGORIES = {
    "tractors",
    "tillage",
    "harvesting",
    "irrigation",
    "spraying",
    "transport",
    "other",
}


class EnquiryIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    phone: str = Field(..., min_length=7, max_length=20)
    message: str = Field("", max_length=500)
