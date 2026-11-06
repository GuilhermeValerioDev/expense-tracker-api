from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    hash_password,
    verify_and_update_password,
    verify_dummy_password,
)
from app.models import User
from app.schemas import UserCreate


def register_user(db: Session, payload: UserCreate) -> User:
    existing = db.execute(select(User).where(User.email == payload.email)).scalars().one_or_none()
    if existing is not None:
        raise ConflictError("Email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Covers the race where another request registered the same email.
        db.rollback()
        raise ConflictError("Email already registered") from exc

    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    user = db.execute(select(User).where(User.email == normalized_email)).scalars().one_or_none()

    if user is None:
        verify_dummy_password(password)
        raise AuthenticationError("Invalid credentials")

    verified, updated_hash = verify_and_update_password(password, user.password_hash)
    if not verified:
        raise AuthenticationError("Invalid credentials")

    if updated_hash is not None:
        # The hashing parameters changed: transparently upgrade the stored hash.
        user.password_hash = updated_hash
        db.commit()

    return user
