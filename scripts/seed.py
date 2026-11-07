import argparse
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import User
from app.schemas import ExpenseCreate, UserCreate
from app.services import auth as auth_service
from app.services import expenses as expense_service

CATEGORIES: dict[str, list[str]] = {
    "food": ["Coffee", "Groceries", "Lunch", "Dinner", "Bakery"],
    "transport": ["Metro card", "Fuel", "Taxi", "Parking"],
    "housing": ["Rent", "Electricity", "Internet", "Water"],
    "health": ["Pharmacy", "Gym", "Dentist", "Health insurance"],
    "entertainment": ["Cinema", "Streaming", "Concert", "Book"],
    "shopping": ["Clothes", "Shoes", "Headphones", "Home supplies"],
    "utilities": ["Phone bill", "Cloud storage", "Software subscription"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the database with demo data.")
    parser.add_argument("--email", default="demo@example.com")
    parser.add_argument("--password", default="demo-password-123")
    parser.add_argument("--count", type=int, default=30, help="Number of expenses to create")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the demo user if it already exists",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.count < 1:
        print("--count must be at least 1")
        return 1

    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == args.email)).scalars().one_or_none()
        if existing is not None:
            if not args.reset:
                print(f"User {args.email} already exists. Use --reset to recreate it.")
                return 1
            db.delete(existing)
            db.commit()

        user = auth_service.register_user(
            db,
            UserCreate(
                username="Demo User",
                email=args.email,
                password=args.password,
            ),
        )

        rng = random.Random(42)
        now = datetime.now(UTC).replace(tzinfo=None)
        categories = list(CATEGORIES)

        for _ in range(args.count):
            category = rng.choice(categories)
            expense_service.create_expense(
                db,
                user,
                ExpenseCreate(
                    name=rng.choice(CATEGORIES[category]),
                    category=category,
                    amount=Decimal(rng.randint(500, 15000)) / Decimal(100),
                    expense_date=now
                    - timedelta(
                        days=rng.randint(0, 180),
                        hours=rng.randint(0, 23),
                        minutes=rng.randint(0, 59),
                    ),
                ),
            )

    print(f"Created {args.count} expenses for {args.email}")
    print(f"Password: {args.password}")
    print()
    print("Try it:")
    print(
        "  curl -s -X POST http://localhost:8000/api/v1/auth/login "
        f"-d 'username={args.email}&password={args.password}'"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
