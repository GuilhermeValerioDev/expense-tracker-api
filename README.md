# Expense Tracker API

[![CI](https://github.com/GuilhermeValerioDev/expense-tracker-api/actions/workflows/ci.yml/badge.svg)](https://github.com/GuilhermeValerioDev/expense-tracker-api/actions/workflows/ci.yml)

A RESTful Expense Tracker API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

This project is my primary backend portfolio project. It is built incrementally with an
emphasis on understanding the design decisions behind authentication, authorization,
database design, and API architecture rather than reproducing tutorial code.

## Features

- JWT authentication (OAuth2 password flow) with Argon2 password hashing
- User registration and login
- Self-service account management at `/api/v1/users/me`
- User-scoped authorization: every expense query is filtered by the authenticated user
- Expense CRUD with request/response validation
- Pagination, filtering by category and date range, and sorting
- Spending summaries grouped by category or month
- Demo seed script and Makefile shortcuts for local walkthroughs
- Versioned API under `/api/v1` with a layered architecture
- Schema migrations with Alembic
- Health and readiness endpoints
- Rate limiting on login and registration
- Request IDs, structured JSON logging, and configurable CORS
- Production Compose overlay with a Caddy TLS reverse proxy
- Backup and restore scripts with a deployment runbook
- PostgreSQL integration with SQLAlchemy 2.0 typed mappings
- Automated tests against PostgreSQL, linting, type checking, and CI

## Tech stack

| Area | Tools |
| --- | --- |
| Runtime | Python 3.13, FastAPI, Uvicorn |
| Data | PostgreSQL 16, SQLAlchemy 2.0, psycopg 3, Alembic |
| Validation | Pydantic 2, pydantic-settings |
| Auth | PyJWT, pwdlib (Argon2) |
| Tooling | uv, pytest, ruff, mypy, pre-commit |
| Hardening | slowapi (rate limiting), CORS, request IDs, JSON logs |
| Infrastructure | Docker, Docker Compose, Caddy, GitHub Actions |

## Architecture

The application is organized in layers so HTTP concerns stay separate from business logic:

| Layer | Responsibility |
| --- | --- |
| `app/api/` | Routing, dependencies, request/response handling |
| `app/services/` | Business rules and database operations |
| `app/models/` | SQLAlchemy tables and relationships |
| `app/schemas/` | Pydantic request/response contracts |
| `app/core/` | Settings, security primitives, domain exceptions |
| `app/db/` | Engine, session factory, `Base` |

Routers depend on services; services raise domain exceptions (`NotFoundError`,
`ConflictError`, `AuthenticationError`) that `app/api/error_handlers.py` translates into HTTP
responses. This keeps business logic independent of FastAPI and reusable outside HTTP.

Application routes are versioned under `/api/v1`. `/health`, `/health/ready`, and `/` remain
unversioned for infrastructure and discovery.

### Data model

```mermaid
erDiagram
    USER ||--o{ EXPENSE : owns
    USER {
        int id PK
        string username
        string email UK
        string password_hash
        datetime created_at
    }
    EXPENSE {
        int id PK
        int user_id FK
        numeric amount
        string category
        string name
        datetime expense_date
        datetime created_at
    }
```

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
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The API is available at <http://localhost:8000>, with interactive docs at
<http://localhost:8000/docs>.

### 3. Or run the whole stack with Docker

```bash
docker compose up --build
```

Compose starts PostgreSQL, waits for it to become healthy, runs the `migrate` service
(`alembic upgrade head`), and only starts the API once migrations have completed.

### 4. Production-style run (local)

The production overlay runs the API behind Caddy, with the API and database ports closed to
the host:

```bash
docker compose -f compose.yml -f compose.prod.yml up --build
curl http://localhost/health/ready
```

Set `SITE_ADDRESS` to a real domain to enable automatic TLS when deploying. See
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the full runbook, backup/restore procedure,
updates, and rollback.

### 5. Seed demo data

```bash
uv run python -m scripts.seed --reset
```

This creates `demo@example.com` / `demo-password-123` with 30 expenses spread over the last
six months. It is intended for local development; `--reset` deletes and recreates the demo
account.

### Common commands

| Command | What it does |
| --- | --- |
| `make dev` | Start PostgreSQL, apply migrations, run the API with reload |
| `make test` | Run the test suite with coverage |
| `make check` | Lint, format check, type check, and tests |
| `make migrate` | Apply migrations |
| `make seed` | Recreate the demo account and expenses |
| `make prod` | Run the production-style stack behind Caddy |
| `make backup` | Create a database dump |

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | SQLAlchemy connection string, e.g. `postgresql+psycopg://user:pass@localhost:5432/expense_tracker` |
| `SECRET_KEY` | yes | Key used to sign JWTs. Use a long random value in production. |
| `POSTGRES_USER` | Compose | PostgreSQL user created by the database container |
| `POSTGRES_PASSWORD` | Compose | PostgreSQL password |
| `POSTGRES_DB` | Compose | PostgreSQL database name |
| `TEST_DATABASE_URL` | no | Overrides the test database. Defaults to `<database>_test` on `localhost`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Access-token lifetime in minutes (default `30`, max `1440`). |
| `SITE_ADDRESS` | Compose | Caddy site address. `http://localhost` locally; a domain in production. |
| `CORS_ORIGINS` | no | JSON list of allowed browser origins, e.g. `["https://app.example.com"]`. |

## API overview

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | – | Create an account |
| `POST` | `/api/v1/auth/login` | – | Log in with `username` (email) and `password`, receive a JWT |
| `GET` | `/api/v1/users/me` | Bearer | Read the current user |
| `PATCH` | `/api/v1/users/me` | Bearer | Update username, email, or password |
| `DELETE` | `/api/v1/users/me` | Bearer | Delete the current account and its expenses |
| `POST` | `/api/v1/expenses/` | Bearer | Create an expense |
| `GET` | `/api/v1/expenses/` | Bearer | List the current user's expenses (paginated, filterable) |
| `GET` | `/api/v1/expenses/summary` | Bearer | Totals grouped by category or month |
| `GET` | `/api/v1/expenses/{id}` | Bearer | Read one of the current user's expenses |
| `PATCH` | `/api/v1/expenses/{id}` | Bearer | Partially update one of the current user's expenses |
| `DELETE` | `/api/v1/expenses/{id}` | Bearer | Delete one of the current user's expenses |
| `GET` | `/health` | – | Liveness probe |
| `GET` | `/health/ready` | – | Readiness probe (checks the database) |

### Authentication flow

1. Register with `POST /api/v1/auth/register`.
2. Log in with `POST /api/v1/auth/login` using form fields `username` (your email) and `password`.
3. Send the returned token as `Authorization: Bearer <token>`.

Changing your email or password requires your current password, so a leaked token cannot
be used to lock you out of your account.

Access tokens expire after 30 minutes by default; set `ACCESS_TOKEN_EXPIRE_MINUTES` to
change that. Request bodies reject unknown fields, and emails, passwords, amounts, and
required fields are validated before they reach the database.

`PATCH /api/v1/expenses/{id}` applies only the fields you send. Send `{"name": null}` to clear the
optional name; required fields such as `amount` cannot be set to null.

### Pagination and filtering

`GET /api/v1/expenses/` accepts the following query parameters:

| Parameter | Default | Description |
| --- | --- | --- |
| `limit` | `20` | Page size, between 1 and 100 |
| `offset` | `0` | Number of records to skip |
| `category` | – | Exact category match |
| `start_date` | – | Inclusive ISO-8601 lower bound for `expense_date` |
| `end_date` | – | Inclusive ISO-8601 upper bound for `expense_date` |
| `order` | `desc` | Sort by `expense_date`, either `asc` or `desc` |

The response is an envelope so clients can paginate without guessing:

```json
{
  "items": [
    {
      "id": 3,
      "user_id": 1,
      "name": "Coffee",
      "category": "food",
      "amount": "4.50",
      "expense_date": "2026-03-01T10:30:00",
      "created_at": "2026-03-01T13:00:00"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

`total` is the count after filters are applied, so it is the value to use for pagination
controls. An inverted date range (`start_date` after `end_date`) returns 422.

### Spending summary

`GET /api/v1/expenses/summary` aggregates the authenticated user's expenses:

| Parameter | Default | Description |
| --- | --- | --- |
| `group_by` | `category` | `category` or `month` (keys look like `2026-03`) |
| `start_date` | – | Inclusive ISO-8601 lower bound |
| `end_date` | – | Inclusive ISO-8601 upper bound |

```json
{
  "group_by": "category",
  "total": "182.40",
  "items": [
    { "key": "food", "total": "120.00", "count": 8 },
    { "key": "transport", "total": "62.40", "count": 3 }
  ]
}
```

The same date-range validation applies: an inverted range returns 422.

## Screenshots

<!-- Add Imgur links here once available. Suggested: Swagger UI, expense list, summary. -->

## Migrations

```bash
uv run alembic upgrade head                                  # apply migrations
uv run alembic revision --autogenerate -m "describe change"  # create a migration
uv run alembic check                                         # detect model/schema drift
```

The application no longer creates tables on startup; run `alembic upgrade head` before
starting it against a new database.

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
├── alembic/
│   ├── versions/              # Database migrations
│   └── env.py                 # Loads settings and model metadata
├── app/
│   ├── api/
│   │   ├── deps.py            # SessionDep, CurrentUser
│   │   ├── error_handlers.py  # Domain/database errors → HTTP
│   │   ├── routes/health.py   # Unversioned health endpoints
│   │   └── v1/
│   │       ├── router.py      # /api/v1 aggregate router
│   │       └── routes/        # auth, users, expenses
│   ├── core/
│   │   ├── config.py          # Typed environment settings
│   │   ├── security.py        # Password hashing and JWT
│   │   └── exceptions.py      # Domain exceptions
│   ├── db/
│   │   ├── base.py            # Declarative Base
│   │   └── session.py         # Engine, session factory, get_db
│   ├── models/                # User and Expense ORM models
│   ├── schemas/               # Pydantic request/response contracts
│   ├── services/              # Business logic and database operations
│   └── main.py                # create_app() and root endpoint
├── tests/
│   ├── api/                   # Endpoint tests
│   ├── core/                  # Settings tests
│   └── db/                    # Schema and constraint tests
├── docs/DEPLOYMENT.md         # VPS runbook, backups, rollback
├── scripts/
│   ├── backup.sh              # pg_dump wrapper
│   ├── restore.sh             # pg_restore wrapper
│   └── seed.py                # Demo account and expenses
├── alembic.ini                # Alembic configuration
├── Caddyfile                  # Reverse proxy / TLS configuration
├── compose.yml                # Development stack
├── compose.prod.yml           # Production overlay (Caddy, no public DB/API ports)
├── Makefile                   # Common development and operations commands
└── pyproject.toml             # Dependencies, tool configuration
```

## Design decisions and trade-offs

- **Layered architecture.** `api → services → models/schemas` keeps HTTP concerns separate
  from business logic, so services can be reused by scripts and future workers.
- **Domain exceptions.** Services raise `NotFoundError`, `ConflictError`,
  `AuthenticationError`, and `ValidationError`; the HTTP layer maps them to responses.
- **Alembic instead of `create_all`.** Schema history is reviewable and reversible, and CI
  fails when models and migrations drift.
- **PostgreSQL-only tests.** SQLite would hide numeric behavior, constraint checks, and
  index semantics.
- **Offset pagination.** Simple and supports page jumps, but large offsets get slower and
  pages can shift when rows are inserted. Keyset pagination is the next step at scale.
- **Access tokens only.** Short-lived JWTs with Argon2 hashing; refresh tokens and
  revocation are a future hardening step.
- **In-memory rate limiting.** Correct for one API process; Redis is needed for multiple
  workers or replicas.
- **Free-text categories.** Deliberately simple for now; first-class categories, budgets,
  and income tracking are the next domain features.

## Roadmap

- [x] JWT authentication and password hashing
- [x] Expense CRUD with user-scoped authorization
- [x] Automated tests, linting, type checking, and CI
- [x] Docker Compose development environment
- [x] Typed settings, strict request validation, and database constraints
- [x] Alembic database migrations
- [x] Pagination, filtering, and sorting for expenses
- [x] Service layer and a consistent `app/` package layout
- [x] Login rate limiting, request IDs, CORS and structured logging
- [x] Production Compose, Caddy reverse proxy and backup/restore tooling
- [x] Spending summaries by category and month
- [x] Demo seed script, Makefile shortcuts and portfolio documentation
- [ ] Income tracking, categories as first-class data, and budgets
- [ ] Refresh tokens and token revocation
- [ ] Deploy to a VPS with TLS and off-site backups

## License

MIT — see [LICENSE](LICENSE).
