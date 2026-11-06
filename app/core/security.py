from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import AuthenticationError

password_hasher = PasswordHash.recommended()

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Verified against when the email is unknown so that login latency does not
# reveal whether an account exists.
_DUMMY_PASSWORD_HASH = password_hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def verify_and_update_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    return password_hasher.verify_and_update(password, password_hash)


def verify_dummy_password(password: str) -> None:
    password_hasher.verify(password, _DUMMY_PASSWORD_HASH)


def create_access_token(user_id: int) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdigit():
            raise AuthenticationError()
        return int(subject)
    except InvalidTokenError as exc:
        raise AuthenticationError() from exc
