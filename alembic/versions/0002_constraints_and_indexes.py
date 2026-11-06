"""add constraints, indexes and cascade delete

Revision ID: 0002_constraints_and_indexes
Revises: 0001_baseline
Create Date: 2026-11-06

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_constraints_and_indexes"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(),
        type_=sa.String(length=320),
        existing_nullable=False,
    )
    op.alter_column(
        "expenses",
        "category",
        existing_type=sa.String(),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        "expenses",
        "name",
        existing_type=sa.String(),
        type_=sa.String(length=100),
        existing_nullable=True,
    )

    op.create_check_constraint(
        "ck_expenses_amount_positive",
        "expenses",
        "amount > 0",
    )
    op.create_index(
        "ix_expenses_user_id_expense_date",
        "expenses",
        ["user_id", "expense_date"],
    )
    op.create_index(
        "ix_expenses_user_id_category",
        "expenses",
        ["user_id", "category"],
    )

    op.drop_constraint("expenses_user_id_fkey", "expenses", type_="foreignkey")
    op.create_foreign_key(
        "expenses_user_id_fkey",
        "expenses",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("expenses_user_id_fkey", "expenses", type_="foreignkey")
    op.create_foreign_key(
        "expenses_user_id_fkey",
        "expenses",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_index("ix_expenses_user_id_category", table_name="expenses")
    op.drop_index("ix_expenses_user_id_expense_date", table_name="expenses")
    op.drop_constraint("ck_expenses_amount_positive", "expenses", type_="check")

    op.alter_column(
        "expenses",
        "name",
        existing_type=sa.String(length=100),
        type_=sa.String(),
        existing_nullable=True,
    )
    op.alter_column(
        "expenses",
        "category",
        existing_type=sa.String(length=50),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=320),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=50),
        type_=sa.String(),
        existing_nullable=False,
    )
