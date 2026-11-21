"""Validation rules for the scheme guidance module."""

from pydantic import BaseModel, Field

VALID_SCHEME_CATEGORIES = {
    "official",
    "eligibility",
    "documents",
    "application",
    "help",
}

VALID_SCHEME_LEVELS = {"central", "state"}
VALID_SCHEME_STATES = {"Andhra Pradesh", "Telangana"}


class QuestionIn(BaseModel):
    question: str = Field(..., min_length=3, max_length=300)
