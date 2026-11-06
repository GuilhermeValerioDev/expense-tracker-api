from fastapi import FastAPI

from app.api.error_handlers import register_exception_handlers
from app.api.routes.health import router as health_router
from app.api.v1.router import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Expense Tracker API",
        description=(
            "A RESTful API for tracking personal expenses. "
            "Register, log in with a JWT, and manage your own expenses."
        ),
        version="0.1.0",
    )

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(v1_router)

    @app.get("/", tags=["meta"])
    def read_root() -> dict[str, str]:
        return {"service": "expense-tracker-api", "docs": "/docs", "health": "/health"}

    return app


app = create_app()
