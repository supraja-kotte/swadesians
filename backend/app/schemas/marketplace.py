"""Validation rules for marketplace enquiries."""

from pydantic import BaseModel, Field

VALID_MARKETPLACE_CATEGORIES = {
    "grains",
    "pulses",
    "vegetables",
    "fruits",
    "oils",
    "spices",
    "other",
}


class EnquiryIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    phone: str = Field(..., min_length=7, max_length=20)
    quantity: str = Field("", max_length=60)
    message: str = Field("", max_length=500)
