from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models import Expense
from app.schemas import (
    ExpenseCreate,
    ExpensePage,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
)
from app.services import expenses as expense_service

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: SessionDep,
    current_user: CurrentUser,
) -> Expense:
    return expense_service.create_expense(db, current_user, payload)


@router.get("/", response_model=ExpensePage)
def list_expenses(
    current_user: CurrentUser,
    db: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    category: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    order: Literal["asc", "desc"] = "desc",
) -> ExpensePage:
    return expense_service.list_expenses(
        db,
        current_user,
        limit=limit,
        offset=offset,
        category=category,
        start_date=start_date,
        end_date=end_date,
        order=order,
    )


@router.get("/summary", response_model=ExpenseSummary)
def summarize_expenses(
    current_user: CurrentUser,
    db: SessionDep,
    group_by: Literal["category", "month"] = "category",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> ExpenseSummary:
    return expense_service.summarize_expenses(
        db,
        current_user,
        group_by=group_by,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: CurrentUser,
    db: SessionDep,
) -> Expense:
    return expense_service.get_expense(db, current_user, expense_id)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    current_user: CurrentUser,
    db: SessionDep,
) -> Expense:
    return expense_service.update_expense(db, current_user, expense_id, payload)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: CurrentUser,
    db: SessionDep,
) -> None:
    expense_service.delete_expense(db, current_user, expense_id)
