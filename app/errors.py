from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


def register_exception_handlers(app: FastAPI) -> None:
    """Map database failures to safe HTTP responses."""

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(
        _request: Request,
        _exc: IntegrityError,
    ) -> JSONResponse:
        # Catch-all for conflicts that were not handled in a route. The
        # details are intentionally generic so internals are never leaked.
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "The request conflicts with existing data."},
        )
