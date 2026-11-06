import pytest
from pydantic import ValidationError

from app.core.config import Settings

DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/expense_tracker"


def _settings(secret_key: str = "x" * 32) -> Settings:
    return Settings(
        _env_file=None,
        database_url=DATABASE_URL,
        secret_key=secret_key,
    )


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

    settings = _settings()

    assert settings.access_token_expire_minutes == 30
    assert settings.test_database_url is None


def test_settings_reject_short_secret() -> None:
    with pytest.raises(ValidationError):
        _settings(secret_key="too-short")


def test_settings_reject_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        _settings(secret_key="replace-this-with-a-long-random-string-at-least-32-characters")


def test_settings_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@db:5432/other")
    monkeypatch.setenv("SECRET_KEY", "y" * 40)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")

    settings = Settings(_env_file=None)

    assert settings.database_url.endswith("/other")
    assert settings.access_token_expire_minutes == 15
