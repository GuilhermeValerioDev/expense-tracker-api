from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routers.auth import get_current_user, password_hasher
from database import get_db
from models import User
from schemas import UserResponse, UserUpdateMe

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    update: UserUpdateMe,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    email_changed = update.email is not None and update.email != current_user.email
    password_changed = update.password is not None

    if (email_changed or password_changed) and (
        update.current_password is None
        or not password_hasher.verify(
            update.current_password,
            current_user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is required to change your email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if update.username is not None:
        current_user.username = update.username

    if email_changed and update.email is not None:
        current_user.email = update.email

    if password_changed and update.password is not None:
        current_user.password_hash = password_hasher.hash(update.password)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc

    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    db.delete(current_user)
    db.commit()
