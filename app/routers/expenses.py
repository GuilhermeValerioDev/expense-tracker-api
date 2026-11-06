from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.routers.auth import get_current_user
from database import get_db
from models import Expense, User
from schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _get_owned_expense(expense_id: int, user: User, db: Session) -> Expense:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Expense:
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
) -> list[Expense]:
    expenses = db.execute(select(Expense).where(Expense.user_id == current_user.id)).scalars().all()
    return list(expenses)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_single_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Expense:
    return _get_owned_expense(expense_id, current_user, db)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    update_info: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Expense:
    current_expense = _get_owned_expense(expense_id, current_user, db)

    # Only fields explicitly sent by the client are applied. This lets a
    # nullable field such as "name" be cleared with an explicit null, while
    # required fields still reject null.
    updates = update_info.model_dump(exclude_unset=True)
    for field in ("category", "amount", "expense_date"):
        if field in updates and updates[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{field} cannot be null",
            )

    for field, value in updates.items():
        setattr(current_expense, field, value)

    db.commit()
    db.refresh(current_expense)
    return current_expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    expense = _get_owned_expense(expense_id, current_user, db)
    db.delete(expense)
    db.commit()
