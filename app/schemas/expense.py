from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import RequestModel, strip_value

Category = Annotated[str, Field(min_length=1, max_length=50)]


class ExpenseCreate(RequestModel):
    name: Annotated[str, Field(max_length=100)] | None = None
    category: Category
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    expense_date: datetime

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return strip_value(value)


class ExpenseUpdate(RequestModel):
    name: Annotated[str, Field(max_length=100)] | None = None
    category: Category | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    expense_date: datetime | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return strip_value(value)


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    name: str | None
    category: str
    amount: Decimal
    expense_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpensePage(BaseModel):
    items: list[ExpenseResponse]
    total: int
    limit: int
    offset: int
