from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError


def register_exception_handlers(app: FastAPI) -> None:
    """Map application and database errors to safe HTTP responses."""

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(
        _request: Request,
        _exc: IntegrityError,
    ) -> JSONResponse:
        # Catch-all for conflicts that were not handled in a service. The
        # details are intentionally generic so internals are never leaked.
        return JSONResponse(
            status_code=409,
            content={"detail": "The request conflicts with existing data."},
        )
