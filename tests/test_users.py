from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Expense

PASSWORD = "password123"
NEW_PASSWORD = "even-better-password"


def test_public_user_routes_are_gone(client: TestClient) -> None:
    assert client.get("/users/").status_code == 404
    assert client.get("/users/1").status_code == 404
    assert client.put("/users/1", json={"username": "x"}).status_code == 404
    assert client.delete("/users/1").status_code == 404


def test_get_me_requires_authentication(client: TestClient) -> None:
    assert client.get("/users/me").status_code == 401


def test_get_me_returns_current_user(
    client: TestClient,
    user: dict[str, Any],
    headers: dict[str, str],
) -> None:
    response = client.get("/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]
    assert response.json()["email"] == user["email"]


def test_update_username_does_not_require_password(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.patch("/users/me", json={"username": "alice-renamed"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == "alice-renamed"


def test_update_email_requires_current_password(
    client: TestClient, headers: dict[str, str]
) -> None:
    response = client.patch("/users/me", json={"email": "new@example.com"}, headers=headers)

    assert response.status_code == 401


def test_update_email_rejects_wrong_current_password(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.patch(
        "/users/me",
        json={"email": "new@example.com", "current_password": "wrong-password"},
        headers=headers,
    )

    assert response.status_code == 401


def test_update_email_with_correct_password(
    client: TestClient,
    headers: dict[str, str],
    login: Any,
) -> None:
    response = client.patch(
        "/users/me",
        json={"email": "new@example.com", "current_password": PASSWORD},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    # The new email is now the login identifier.
    assert login("new@example.com")


def test_update_email_rejects_another_users_email(
    client: TestClient,
    headers: dict[str, str],
    register_user: Any,
) -> None:
    register_user(username="bob", email="bob@example.com")

    response = client.patch(
        "/users/me",
        json={"email": "bob@example.com", "current_password": PASSWORD},
        headers=headers,
    )

    assert response.status_code == 409
    # The failed write must not poison the session for subsequent requests.
    assert client.get("/users/me", headers=headers).status_code == 200


def test_update_rejects_unknown_fields(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.patch("/users/me", json={"is_admin": True}, headers=headers)

    assert response.status_code == 422


def test_change_password_rotates_credentials(
    client: TestClient,
    headers: dict[str, str],
    user: dict[str, Any],
) -> None:
    response = client.patch(
        "/users/me",
        json={"password": NEW_PASSWORD, "current_password": PASSWORD},
        headers=headers,
    )
    assert response.status_code == 200

    old_login = client.post(
        "/auth/login",
        data={"username": user["email"], "password": PASSWORD},
    )
    new_login = client.post(
        "/auth/login",
        data={"username": user["email"], "password": NEW_PASSWORD},
    )

    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_delete_me_requires_authentication(client: TestClient) -> None:
    assert client.delete("/users/me").status_code == 401


def test_delete_me_removes_account_and_invalidates_token(
    client: TestClient,
    headers: dict[str, str],
    user: dict[str, Any],
) -> None:
    response = client.delete("/users/me", headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/users/me", headers=headers).status_code == 401

    relogin = client.post(
        "/auth/login",
        data={"username": user["email"], "password": PASSWORD},
    )
    assert relogin.status_code == 401


def test_delete_me_cascades_expenses(
    client: TestClient,
    headers: dict[str, str],
    user: dict[str, Any],
    db_session: Session,
) -> None:
    create = client.post(
        "/expenses/",
        json={
            "name": "Coffee",
            "category": "food",
            "amount": "4.50",
            "expense_date": "2026-01-15T10:30:00",
        },
        headers=headers,
    )
    assert create.status_code == 201

    assert client.delete("/users/me", headers=headers).status_code == 204

    remaining = db_session.execute(
        select(func.count()).select_from(Expense).where(Expense.user_id == user["id"])
    ).scalar_one()
    assert remaining == 0
