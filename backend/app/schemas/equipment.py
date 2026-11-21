"""Validation rules for owner-submitted listings, renter profiles and enquiries."""

from pydantic import BaseModel, Field, field_validator

VALID_EQUIPMENT_CATEGORIES = {
    "tractors",
    "tillage",
    "harvesting",
    "irrigation",
    "spraying",
    "transport",
    "other",
}
VALID_PRICE_UNITS = {"hour", "day", "season"}
OWNER_LISTING_STATUSES = {"active", "paused"}
ADMIN_LISTING_STATUSES = {"active", "hidden"}
VALID_ENQUIRY_STATUSES = {"new", "contacted", "closed"}
VALID_PROVIDER_STATUSES = {"active", "paused"}


def _check_choice(value: str | None, allowed: set[str]) -> str | None:
    if value is not None and value not in allowed:
        raise ValueError("Unknown value")
    return value


class ListingIn(BaseModel):
    category: str
    title: str = Field(..., min_length=4, max_length=120)
    description: str = Field("", max_length=800)
    state: str = Field(..., min_length=2, max_length=60)
    district: str = Field(..., min_length=2, max_length=60)
    price_amount: int = Field(..., gt=0, le=10_000_000)
    price_unit: str
    owner_label: str = Field(..., min_length=2, max_length=60)
    owner_contact: str = Field(..., min_length=5, max_length=120)
    availability: str = Field("", max_length=120)
    owner_key: str = Field(..., min_length=16, max_length=128)

    @field_validator("category")
    @classmethod
    def check_category(cls, value: str) -> str:
        return _check_choice(value, VALID_EQUIPMENT_CATEGORIES) or value

    @field_validator("price_unit")
    @classmethod
    def check_price_unit(cls, value: str) -> str:
        return _check_choice(value, VALID_PRICE_UNITS) or value


class ListingUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=4, max_length=120)
    description: str | None = Field(None, max_length=800)
    state: str | None = Field(None, min_length=2, max_length=60)
    district: str | None = Field(None, min_length=2, max_length=60)
    price_amount: int | None = Field(None, gt=0, le=10_000_000)
    price_unit: str | None = Field(None, max_length=20)
    owner_label: str | None = Field(None, min_length=2, max_length=60)
    owner_contact: str | None = Field(None, min_length=5, max_length=120)
    availability: str | None = Field(None, max_length=120)
    status: str | None = Field(None, max_length=20)

    @field_validator("price_unit")
    @classmethod
    def check_price_unit(cls, value: str | None) -> str | None:
        return _check_choice(value, VALID_PRICE_UNITS)

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        return _check_choice(value, OWNER_LISTING_STATUSES)


class EnquiryIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    phone: str = Field(..., min_length=7, max_length=20)
    message: str = Field("", max_length=500)
    farmer_key: str = Field(..., min_length=16, max_length=128)


class EnquiryUpdateIn(BaseModel):
    status: str = Field(..., max_length=20)
    reply: str = Field("", max_length=300)

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        return _check_choice(value, VALID_ENQUIRY_STATUSES) or value


class AdminListingStatusIn(BaseModel):
    status: str = Field(..., max_length=20)

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        return _check_choice(value, ADMIN_LISTING_STATUSES) or value


class ProviderIn(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=60)
    contact: str = Field(..., min_length=5, max_length=120)
    state: str = Field(..., min_length=2, max_length=60)
    district: str = Field(..., min_length=2, max_length=60)
    categories: list[str] = Field(..., min_length=1, max_length=7)
    availability: str = Field("", max_length=120)
    description: str = Field("", max_length=500)
    status: str = Field("active", max_length=20)

    @field_validator("categories")
    @classmethod
    def check_categories(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            category = _check_choice(item.strip(), VALID_EQUIPMENT_CATEGORIES)
            if category and category not in cleaned:
                cleaned.append(category)
        if not cleaned:
            raise ValueError("At least one equipment category is required")
        return cleaned

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        return _check_choice(value, VALID_PROVIDER_STATUSES) or value


class ProviderEnquiryIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    phone: str = Field(..., min_length=7, max_length=20)
    message: str = Field("", max_length=500)
    farmer_key: str = Field(..., min_length=16, max_length=128)


class ProviderEnquiryUpdateIn(BaseModel):
    status: str = Field(..., max_length=20)
    reply: str = Field("", max_length=300)

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        return _check_choice(value, VALID_ENQUIRY_STATUSES) or value
