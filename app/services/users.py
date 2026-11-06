from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import hash_password, verify_password
from app.models import User
from app.schemas import UserUpdateMe


def update_profile(db: Session, user: User, payload: UserUpdateMe) -> User:
    email_changed = payload.email is not None and payload.email != user.email
    password_changed = payload.password is not None

    if (email_changed or password_changed) and (
        payload.current_password is None
        or not verify_password(payload.current_password, user.password_hash)
    ):
        raise AuthenticationError("Current password is required to change your email or password")

    if payload.username is not None:
        user.username = payload.username

    if email_changed and payload.email is not None:
        user.email = payload.email

    if password_changed and payload.password is not None:
        user.password_hash = hash_password(payload.password)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Email already registered") from exc

    db.refresh(user)
    return user


def delete_account(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
