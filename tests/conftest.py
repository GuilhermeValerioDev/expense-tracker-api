from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.session import get_db
from app.main import app

DEFAULT_PASSWORD = "password123"


def _test_database_url() -> str:
    if settings.test_database_url:
        return settings.test_database_url

    url = make_url(settings.database_url)
    if url.get_backend_name() != "postgresql":
        return url.render_as_string(hide_password=False)

    # Tests run against a separate database on the local server, regardless of
    # whether DATABASE_URL points at the Docker host name.
    return url.set(host="localhost", database=f"{url.database}_test").render_as_string(
        hide_password=False
    )


def _ensure_database_exists(url: str) -> None:
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql":
        return

    admin_engine = create_engine(
        parsed.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": parsed.database},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{parsed.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Generator[Engine]:
    url = _test_database_url()
    _ensure_database_exists(url)

    test_engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture(autouse=True)
def _clean_database(engine: Engine) -> Generator[None]:
    yield
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE expenses, users RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> Generator[None]:
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def register_user(client: TestClient) -> Any:
    def _register(
        username: str = "alice",
        email: str = "alice@example.com",
        password: str = DEFAULT_PASSWORD,
    ) -> dict[str, Any]:
        response = client.post(
            "/api/v1/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _register


@pytest.fixture
def login(client: TestClient) -> Any:
    def _login(email: str, password: str = DEFAULT_PASSWORD) -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture
def user(register_user: Any) -> dict[str, Any]:
    return register_user()


@pytest.fixture
def headers(user: dict[str, Any], login: Any) -> dict[str, str]:
    return login(user["email"])
