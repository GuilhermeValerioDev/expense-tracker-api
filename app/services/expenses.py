from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models import Expense, User
from app.schemas import (
    ExpenseCreate,
    ExpensePage,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseSummaryItem,
    ExpenseUpdate,
)


def _get_owned_expense(db: Session, user: User, expense_id: int) -> Expense:
    expense = (
        db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.user_id == user.id,
            )
        )
        .scalars()
        .one_or_none()
    )
    if expense is None:
        raise NotFoundError("Expense not found")
    return expense


def create_expense(db: Session, user: User, payload: ExpenseCreate) -> Expense:
    expense = Expense(
        user_id=user.id,
        category=payload.category,
        amount=payload.amount,
        name=payload.name,
        expense_date=payload.expense_date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(
    db: Session,
    user: User,
    *,
    limit: int,
    offset: int,
    category: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
    order: Literal["asc", "desc"],
) -> ExpensePage:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValidationError("start_date must be earlier than or equal to end_date")

    filters = [Expense.user_id == user.id]
    if category is not None:
        filters.append(Expense.category == category)
    if start_date is not None:
        filters.append(Expense.expense_date >= start_date)
    if end_date is not None:
        filters.append(Expense.expense_date <= end_date)

    total = db.execute(select(func.count()).select_from(Expense).where(*filters)).scalar_one()

    if order == "asc":
        ordering = (Expense.expense_date.asc(), Expense.id.asc())
    else:
        ordering = (Expense.expense_date.desc(), Expense.id.desc())

    expenses = (
        db.execute(select(Expense).where(*filters).order_by(*ordering).offset(offset).limit(limit))
        .scalars()
        .all()
    )

    return ExpensePage(
        items=[ExpenseResponse.model_validate(expense) for expense in expenses],
        total=total,
        limit=limit,
        offset=offset,
    )


def summarize_expenses(
    db: Session,
    user: User,
    *,
    group_by: Literal["category", "month"],
    start_date: datetime | None,
    end_date: datetime | None,
) -> ExpenseSummary:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValidationError("start_date must be earlier than or equal to end_date")

    filters = [Expense.user_id == user.id]
    if start_date is not None:
        filters.append(Expense.expense_date >= start_date)
    if end_date is not None:
        filters.append(Expense.expense_date <= end_date)

    bucket: Any
    ordering: Any
    if group_by == "category":
        bucket = Expense.category
        ordering = func.sum(Expense.amount).desc()
    else:
        bucket = func.date_trunc("month", Expense.expense_date)
        ordering = bucket.asc()

    rows = db.execute(
        select(
            bucket.label("bucket"),
            func.sum(Expense.amount).label("total"),
            func.count().label("count"),
        )
        .where(*filters)
        .group_by(bucket)
        .order_by(ordering)
    ).all()

    items: list[ExpenseSummaryItem] = []
    grand_total = Decimal("0")
    for row in rows:
        key = str(row.bucket) if group_by == "category" else row.bucket.strftime("%Y-%m")
        items.append(
            ExpenseSummaryItem(
                key=key,
                total=row.total,
                count=row.count,
            )
        )
        grand_total += row.total

    return ExpenseSummary(group_by=group_by, total=grand_total, items=items)


def get_expense(db: Session, user: User, expense_id: int) -> Expense:
    return _get_owned_expense(db, user, expense_id)


def update_expense(
    db: Session,
    user: User,
    expense_id: int,
    payload: ExpenseUpdate,
) -> Expense:
    expense = _get_owned_expense(db, user, expense_id)

    # Only fields explicitly sent by the client are applied. This lets a
    # nullable field such as "name" be cleared with an explicit null, while
    # required fields still reject null.
    updates = payload.model_dump(exclude_unset=True)
    for field in ("category", "amount", "expense_date"):
        if field in updates and updates[field] is None:
            raise ValidationError(f"{field} cannot be null")

    for field, value in updates.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, user: User, expense_id: int) -> None:
    expense = _get_owned_expense(db, user, expense_id)
    db.delete(expense)
    db.commit()
