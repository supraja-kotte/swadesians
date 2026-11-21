"""Validation rules for community requests."""

from typing import Literal

from pydantic import BaseModel, Field

VALID_CATEGORIES = {
    "general",
    "weather",
    "crops",
    "irrigation",
    "schemes",
    "equipment",
    "marketplace",
}


class PostIn(BaseModel):
    author: str = Field("", max_length=60)
    language: str = Field("en", max_length=10)
    category: str = Field("general", max_length=30)
    title: str = Field(..., min_length=3, max_length=140)
    body: str = Field(..., min_length=3, max_length=2000)
    # Optional, returned by POST /api/community/upload. All three must be set
    # together and the path must point at a real file inside the upload folder.
    media_path: str = Field("", max_length=500)
    media_kind: str = Field("", max_length=10)
    media_name: str = Field("", max_length=120)


class ReplyIn(BaseModel):
    author: str = Field("", max_length=60)
    language: str = Field("en", max_length=10)
    body: str = Field(..., min_length=2, max_length=1000)


class ModerationIn(BaseModel):
    status: Literal["published", "hidden"]
