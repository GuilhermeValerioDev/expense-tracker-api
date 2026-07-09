# Expense Tracker API

> 🚧 This project is actively under development and will continue to evolve as I expand it with new backend features and best practices.

A RESTful Expense Tracker API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

This project is my primary backend portfolio project and is being developed incrementally as I learn more advanced backend engineering concepts. Rather than following a tutorial from start to finish, I'm building each feature step by step while focusing on understanding the design decisions behind it.

## Current Features

- JWT Authentication
- Secure password hashing (Argon2 via pwdlib)
- User registration and login
- User CRUD operations
- Expense CRUD operations
- User-scoped authorization
- SQLAlchemy ORM relationships
- PostgreSQL integration
- Pydantic request and response validation

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- python-jose
- pwdlib
- Uvicorn

## Running the project

1. Clone the repository

```bash
git clone <repository-url>
cd expense-tracker-api
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration.

4. Run the server

```bash
uvicorn main:app --reload
```

## Project Roadmap

This project is still actively evolving.

Planned improvements include:

- Authentication refactoring
- Improved project structure
- Filtering and pagination
- Automated testing
- Docker support
- Alembic database migrations
- Better API documentation
- CI/CD pipeline

## Why this project?

I built this project to practice real-world backend development concepts such as authentication, authorization, database design, dependency injection, and REST API architecture.

Every major feature is implemented incrementally with an emphasis on understanding the reasoning behind the implementation rather than simply reproducing tutorial code.