# Expense Tracker API

[![CI](https://github.com/GuilhermeValerioDev/expense-tracker-api/actions/workflows/ci.yml/badge.svg)](https://github.com/GuilhermeValerioDev/expense-tracker-api/actions/workflows/ci.yml)

A RESTful Expense Tracker API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

This project is my primary backend portfolio project. It is built incrementally with an
emphasis on understanding the design decisions behind authentication, authorization,
database design, and API architecture rather than reproducing tutorial code.

## Features

- JWT authentication (OAuth2 password flow) with Argon2 password hashing
- User registration and login
- Self-service account management at `/users/me`
- User-scoped authorization: every expense query is filtered by the authenticated user
- Expense CRUD with request/response validation
- Health and readiness endpoints
- PostgreSQL integration with SQLAlchemy 2.0 typed mappings
- Automated tests against PostgreSQL, linting, type checking, and CI

## Tech stack

| Area | Tools |
| --- | --- |
| Runtime | Python 3.13, FastAPI, Uvicorn |
| Data | PostgreSQL 16, SQLAlchemy 2.0, psycopg 3 |
| Validation | Pydantic 2, pydantic-settings |
| Auth | PyJWT, pwdlib (Argon2) |
| Tooling | uv, pytest, ruff, mypy, pre-commit |
| Infrastructure | Docker, Docker Compose, GitHub Actions |

## Getting started

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL locally, or to run the whole stack)

### 1. Configure the environment

```bash
cp .env.example .env
```

Fill in `SECRET_KEY` and the PostgreSQL credentials. The same `POSTGRES_*` values are used
by both the Compose database and the application connection string.

### 2. Run locally

Start PostgreSQL, install dependencies, and start the API:

```bash
docker compose up -d postgres
uv sync
uv run uvicorn main:app --reload
```

The API is available at <http://localhost:8000>, with interactive docs at
<http://localhost:8000/docs>.

### 3. Or run the whole stack with Docker

```bash
docker compose up --build
```

Compose starts PostgreSQL, waits for it to become healthy, and then starts the API.

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | SQLAlchemy connection string, e.g. `postgresql+psycopg://user:pass@localhost:5432/expense_tracker` |
| `SECRET_KEY` | yes | Key used to sign JWTs. Use a long random value in production. |
| `POSTGRES_USER` | Compose | PostgreSQL user created by the database container |
| `POSTGRES_PASSWORD` | Compose | PostgreSQL password |
| `POSTGRES_DB` | Compose | PostgreSQL database name |
| `TEST_DATABASE_URL` | no | Overrides the test database. Defaults to `<database>_test` on `localhost`. |
| `SKIP_DB_INIT` | no | Set to `1` to skip table creation on startup (used by tests). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Access-token lifetime in minutes (default `30`, max `1440`). |

## API overview

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | – | Create an account |
| `POST` | `/auth/login` | – | Log in with `username` (email) and `password`, receive a JWT |
| `GET` | `/users/me` | Bearer | Read the current user |
| `PATCH` | `/users/me` | Bearer | Update username, email, or password |
| `DELETE` | `/users/me` | Bearer | Delete the current account and its expenses |
| `POST` | `/expenses/` | Bearer | Create an expense |
| `GET` | `/expenses/` | Bearer | List the current user's expenses |
| `GET` | `/expenses/{id}` | Bearer | Read one of the current user's expenses |
| `PATCH` | `/expenses/{id}` | Bearer | Partially update one of the current user's expenses |
| `DELETE` | `/expenses/{id}` | Bearer | Delete one of the current user's expenses |
| `GET` | `/health` | – | Liveness probe |
| `GET` | `/health/ready` | – | Readiness probe (checks the database) |

### Authentication flow

1. Register with `POST /auth/register`.
2. Log in with `POST /auth/login` using form fields `username` (your email) and `password`.
3. Send the returned token as `Authorization: Bearer <token>`.

Changing your email or password requires your current password, so a leaked token cannot
be used to lock you out of your account.

Access tokens expire after 30 minutes by default; set `ACCESS_TOKEN_EXPIRE_MINUTES` to
change that. Request bodies reject unknown fields, and emails, passwords, amounts, and
required fields are validated before they reach the database.

`PATCH /expenses/{id}` applies only the fields you send. Send `{"name": null}` to clear the
optional name; required fields such as `amount` cannot be set to null.

## Tests

Tests run against a real PostgreSQL database (SQLite would hide behavior that matters for
this project, such as numeric types and constraints). The test database is created
automatically from `DATABASE_URL`, or from `TEST_DATABASE_URL` when set.

```bash
docker compose up -d postgres
uv run pytest --cov --cov-report=term-missing
```

Quality checks used by CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Install the git hooks with `uv run pre-commit install`.

## Project structure

```text
.
├── app/
│   ├── routers/          # HTTP layer: auth, users, expenses
│   └── errors.py         # Database exception handlers
├── tests/                # API tests against PostgreSQL
├── config.py             # Environment loading
├── database.py           # Engine, session factory, Base
├── models.py             # SQLAlchemy models
├── schemas.py            # Pydantic request/response schemas
├── main.py               # Application factory, lifespan, health checks
├── compose.yml           # API + PostgreSQL stack
└── pyproject.toml        # Dependencies, tool configuration
```

## Roadmap

- [x] JWT authentication and password hashing
- [x] Expense CRUD with user-scoped authorization
- [x] Automated tests, linting, type checking, and CI
- [x] Docker Compose development environment
- [x] Typed settings, strict request validation, and database constraints
- [ ] Alembic database migrations
- [ ] Pagination, filtering, and sorting for expenses
- [ ] Move business logic into a service layer and package the app consistently
- [ ] Income tracking, categories as first-class data, and spending summaries
- [ ] Refresh tokens, token revocation, and login rate limiting
- [ ] Production deployment behind a reverse proxy with TLS and backups
