from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

import models  # noqa: F401  # registers ORM models on Base.metadata
from app.errors import register_exception_handlers
from app.routers.auth import router as auth_router
from app.routers.expenses import router as expenses_router
from app.routers.users import router as users_router
from config import settings
from database import get_db, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Skipped in tests, where the harness creates the schema itself.
    if not settings.skip_db_init:
        init_db()
    yield


app = FastAPI(
    title="Expense Tracker API",
    description=(
        "A RESTful API for tracking personal expenses. "
        "Register, log in with a JWT, and manage your own expenses."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(users_router)


@app.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {"service": "expense-tracker-api", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
