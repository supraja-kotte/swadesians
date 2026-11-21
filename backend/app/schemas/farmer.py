"""Validation rules for farmer registration and sign-in."""

from pydantic import BaseModel, Field, field_validator


class FarmerRegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    display_name: str = Field("", max_length=60)
    password: str = Field(..., min_length=8, max_length=200)

    @field_validator("username", "display_name", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class FarmerLoginIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8, max_length=200)

    @field_validator("username", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()
