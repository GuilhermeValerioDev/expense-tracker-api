from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.core.security import create_access_token
from app.models import User
from app.schemas import Token, UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: UserCreate, db: SessionDep) -> User:
    return auth_service.register_user(db, payload)


@router.post("/login", response_model=Token)
def login(
    db: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    return Token(access_token=create_access_token(user.id), token_type="bearer")
