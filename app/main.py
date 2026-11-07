from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.error_handlers import register_exception_handlers
from app.api.routes.health import router as health_router
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.logging import RequestContextMiddleware, configure_logging
from app.core.rate_limit import limiter


def _handle_rate_limit(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, RateLimitExceeded):
        raise exc
    return _rate_limit_exceeded_handler(request, exc)


def create_app() -> FastAPI:
    configure_logging(settings.log_json)

    app = FastAPI(
        title="Expense Tracker API",
        description=(
            "A RESTful API for tracking personal expenses. "
            "Register, log in with a JWT, and manage your own expenses."
        ),
        version="1.0.0",
        contact={
            "name": "Guilherme Valerio",
            "url": "https://github.com/GuilhermeValerioDev",
        },
        license_info={"name": "MIT"},
        openapi_tags=[
            {"name": "auth", "description": "Registration and login."},
            {"name": "users", "description": "Self-service account management."},
            {"name": "expenses", "description": "Expense CRUD, filtering and summaries."},
            {"name": "health", "description": "Liveness and readiness probes."},
            {"name": "meta", "description": "Service discovery."},
        ],
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _handle_rate_limit)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Added last so it wraps CORS and the exception handlers.
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(v1_router)

    @app.get("/", tags=["meta"])
    def read_root() -> dict[str, str]:
        return {"service": "expense-tracker-api", "docs": "/docs", "health": "/health"}

    return app


app = create_app()
