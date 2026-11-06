from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.models import User
from app.schemas import UserResponse, UserUpdateMe
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdateMe,
    db: SessionDep,
    current_user: CurrentUser,
) -> User:
    return user_service.update_profile(db, current_user, payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(db: SessionDep, current_user: CurrentUser) -> None:
    user_service.delete_account(db, current_user)
