from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Username = Annotated[str, Field(min_length=1, max_length=50)]
Email = Annotated[EmailStr, Field(max_length=320)]
Password = Annotated[str, Field(min_length=8, max_length=128)]
Category = Annotated[str, Field(min_length=1, max_length=50)]


def _normalize_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


class RequestModel(BaseModel):
    """Base for request bodies: reject unknown fields instead of ignoring them."""

    model_config = ConfigDict(extra="forbid")


class UserCreate(RequestModel):
    username: Username
    email: Email
    password: Password

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: object) -> object:
        return _strip(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return _normalize_email(value)


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
        return _strip(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return _normalize_email(value)


class ExpenseCreate(RequestModel):
    name: Annotated[str, Field(max_length=100)] | None = None
    category: Category
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    expense_date: datetime

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return _strip(value)


class ExpenseUpdate(RequestModel):
    name: Annotated[str, Field(max_length=100)] | None = None
    category: Category | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    expense_date: datetime | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return _strip(value)


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    name: str | None
    category: str
    amount: Decimal
    expense_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
