from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import RequestModel, normalize_email, strip_value

Username = Annotated[str, Field(min_length=1, max_length=50)]
Email = Annotated[EmailStr, Field(max_length=320)]
Password = Annotated[str, Field(min_length=8, max_length=128)]


class UserCreate(RequestModel):
    username: Username
    email: Email
    password: Password

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: object) -> object:
        return strip_value(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: object) -> object:
        return normalize_email(value)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateMe(RequestModel):
    username: Username | None = None
    email: Email | None = None
    password: Password | None = None
    current_password: str | None = None

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: object) -> object:
        return strip_value(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: object) -> object:
        return normalize_email(value)
