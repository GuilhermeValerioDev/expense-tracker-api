from pydantic import BaseModel, ConfigDict


class RequestModel(BaseModel):
    """Base for request bodies: reject unknown fields instead of ignoring them."""

    model_config = ConfigDict(extra="forbid")


def normalize_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


def strip_value(value: object) -> object:
    return value.strip() if isinstance(value, str) else value
