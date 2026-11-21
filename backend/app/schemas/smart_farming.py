"""Validation rules for smart farming field notes."""

from pydantic import BaseModel, Field

VALID_SMART_CATEGORIES = {
    "soil",
    "water",
    "crops",
    "pests",
    "records",
    "weather",
}


class FieldNoteIn(BaseModel):
    field_name: str = Field(..., min_length=2, max_length=60)
    crop: str = Field(..., min_length=2, max_length=60)
    stage: str = Field("", max_length=40)
    observation: str = Field("", max_length=500)
