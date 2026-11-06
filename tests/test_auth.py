from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi.testclient import TestClient

from app.routers.auth import ALGORITHM, SECRET_KEY

DEFAULT_PASSWORD = "password123"


def _token(claims: dict[str, Any]) -> str:
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def test_register_creates_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body


def test_register_normalizes_email_and_username(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "username": "  alice  ",
            "email": "  Alice@Example.COM ",
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert response.json()["email"] == "alice@example.com"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": DEFAULT_PASSWORD,
    }

    assert client.post("/auth/register", json=payload).status_code == 201
    duplicate = client.post("/auth/register", json=payload)

    assert duplicate.status_code == 409


def test_register_rejects_case_variant_duplicate(client: TestClient) -> None:
    assert (
        client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": DEFAULT_PASSWORD,
            },
        ).status_code
        == 201
    )

    duplicate = client.post(
        "/auth/register",
        json={
            "username": "alice2",
            "email": "ALICE@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )

    assert duplicate.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "short"},
    )

    assert response.status_code == 422


def test_register_rejects_invalid_email(client: TestClient) -> None:
    for email in ("alice", "alice@", "@example.com"):
        response = client.post(
            "/auth/register",
            json={"username": "alice", "email": email, "password": DEFAULT_PASSWORD},
        )
        assert response.status_code == 422, email


def test_register_rejects_unknown_fields(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": DEFAULT_PASSWORD,
            "is_admin": True,
        },
    )

    assert response.status_code == 422


def test_login_returns_bearer_token(client: TestClient, user: dict[str, Any]) -> None:
    response = client.post(
        "/auth/login",
        data={"username": user["email"], "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_email_is_case_insensitive(client: TestClient, user: dict[str, Any]) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "ALICE@example.com", "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200


def test_login_rejects_wrong_password(client: TestClient, user: dict[str, Any]) -> None:
    response = client.post(
        "/auth/login",
        data={"username": user["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 401


def test_expired_token_returns_401_not_500(
    client: TestClient,
    user: dict[str, Any],
) -> None:
    token = _token(
        {
            "sub": str(user["id"]),
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        }
    )

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_malformed_token_returns_401(client: TestClient) -> None:
    response = client.get("/users/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401


def test_token_signed_with_wrong_key_returns_401(
    client: TestClient,
    user: dict[str, Any],
) -> None:
    token = jwt.encode(
        {"sub": str(user["id"]), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "wrong-secret-key-that-is-at-least-32-bytes-long",
        algorithm=ALGORITHM,
    )

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_token_with_non_numeric_subject_returns_401(client: TestClient) -> None:
    token = _token(
        {
            "sub": "not-a-number",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        }
    )

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_401_includes_www_authenticate_header(client: TestClient) -> None:
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
