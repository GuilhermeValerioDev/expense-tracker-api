from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings read from the environment or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    secret_key: str = Field(min_length=32)
    test_database_url: str | None = None
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    cors_origins: list[str] = Field(default_factory=list)
    log_json: bool = False

    @field_validator("secret_key")
    @classmethod
    def reject_placeholder_secret(cls, value: str) -> str:
        if value.startswith("replace-this"):
            raise ValueError("SECRET_KEY must be replaced with a real random value")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # values come from the environment


settings = get_settings()
