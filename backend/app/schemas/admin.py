"""Validation rules for administrator sign-in."""

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=8, max_length=200)
