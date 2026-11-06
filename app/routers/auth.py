from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import User
from schemas import Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

password_hasher = PasswordHash.recommended()

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Verified against when the email is unknown so that login latency does not
# reveal whether an account exists.
_DUMMY_PASSWORD_HASH = password_hasher.hash("not-a-real-password")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(user_id: int) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _auth_error(detail: str = "Invalid authentication credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdigit():
            raise _auth_error()
        user_id = int(subject)
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise _auth_error() from exc

    user = db.execute(select(User).where(User.id == user_id)).scalars().one_or_none()
    if user is None:
        raise _auth_error()
    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(user: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.execute(select(User).where(User.email == user.email)).scalars().one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=password_hasher.hash(user.password),
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Covers the race where another request registered the same email.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc

    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    email = form_data.username.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalars().one_or_none()

    if user is None:
        password_hasher.verify(form_data.password, _DUMMY_PASSWORD_HASH)
        raise _auth_error("Invalid credentials")

    verified, updated_hash = password_hasher.verify_and_update(
        form_data.password,
        user.password_hash,
    )
    if not verified:
        raise _auth_error("Invalid credentials")

    if updated_hash is not None:
        # The hashing parameters changed: transparently upgrade the stored hash.
        user.password_hash = updated_hash
        db.commit()

    return Token(access_token=create_access_token(user.id), token_type="bearer")
