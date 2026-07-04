from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None


class ExpenseCreate(BaseModel):
    user_id: int
    name: str | None = None
    category: str
    amount: Decimal
    expense_date: datetime


class ExpenseUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    amount: Decimal | None = None
    expense_date: datetime | None = None


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    name: str | None
    category: str
    amount: Decimal
    expense_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


