from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from models import Expense, User
from database import get_db
from app.routers.auth import get_current_user
from schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_expense = Expense(
        user_id=current_user.id,
        category=expense.category,
        amount=expense.amount,
        name=expense.name,
        expense_date=expense.expense_date,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@router.get("/", response_model=list[ExpenseResponse])
def get_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = (
        db.execute(select(Expense).where(Expense.user_id == current_user.id))
        .scalars()
        .all()
    )
    return result


@router.get("/{id}", response_model=ExpenseResponse)
def get_single_expense(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = (
        db.execute(
            select(Expense).where(
                Expense.id == id,
                Expense.user_id == current_user.id,
            )
        )
        .scalars()
        .one_or_none()
    )

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found.")

    return expense


@router.put("/{id}", response_model=ExpenseResponse)
def update_expense(
    id: int,
    update_info: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_expense = (
        db.execute(
            select(Expense).where(
                Expense.id == id,
                Expense.user_id == current_user.id,
            )
        )
        .scalars()
        .one_or_none()
    )

    if current_expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    if update_info.name is not None:
        current_expense.name = update_info.name

    if update_info.category is not None:
        current_expense.category = update_info.category

    if update_info.amount is not None:
        current_expense.amount = update_info.amount

    if update_info.expense_date is not None:
        current_expense.expense_date = update_info.expense_date

    db.commit()
    db.refresh(current_expense)
    return current_expense


@router.delete("/{id}")
def delete_expense(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = (
        db.execute(
            select(Expense).where(
                Expense.id == id,
                Expense.user_id == current_user.id,
            )
        )
        .scalars()
        .one_or_none()
    )

    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return {"message": f"Deleted expense {id}"}