from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Expense


def test_database_rejects_non_positive_amount(
    db_session: Session,
    user: dict[str, Any],
) -> None:
    expense = Expense(
        user_id=user["id"],
        amount=Decimal("-0.01"),
        category="test",
        expense_date=datetime(2026, 1, 1),
    )
    db_session.add(expense)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_amount_check_constraint_exists(db_session: Session) -> None:
    bind = db_session.get_bind()
    if bind.dialect.name != "postgresql":
        pytest.skip("PostgreSQL-specific schema check")

    names: set[str] = set(
        db_session.execute(
            text("SELECT conname FROM pg_constraint WHERE conrelid = 'expenses'::regclass")
        ).scalars()
    )

    assert "ck_expenses_amount_positive" in names


def test_expense_query_indexes_exist(db_session: Session) -> None:
    bind = db_session.get_bind()
    if bind.dialect.name != "postgresql":
        pytest.skip("PostgreSQL-specific schema check")

    names: set[str] = set(
        db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename = 'expenses'")
        ).scalars()
    )

    assert {
        "ix_expenses_user_id_expense_date",
        "ix_expenses_user_id_category",
    } <= names
