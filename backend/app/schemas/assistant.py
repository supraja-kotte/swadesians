"""Validation rules for the voice command list and natural-language questions."""

from pydantic import BaseModel, Field

from ..config import SUPPORTED_VOICE_LANGUAGES

VALID_COMMAND_CATEGORIES = {
    "navigation",
    "reading",
    "help",
}
VALID_VOICE_LANGUAGES = set(SUPPORTED_VOICE_LANGUAGES)


class AskIn(BaseModel):
    text: str = Field(..., min_length=2, max_length=500)
    language: str = Field(..., min_length=2, max_length=2)
