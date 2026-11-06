class AppError(Exception):
    """Base class for errors that map to HTTP responses."""

    status_code = 500
    detail = "Internal server error"
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    detail = "The request conflicts with existing data"


class AuthenticationError(AppError):
    status_code = 401
    detail = "Invalid authentication credentials"
    headers = {"WWW-Authenticate": "Bearer"}


class ValidationError(AppError):
    status_code = 422
    detail = "Invalid request"
