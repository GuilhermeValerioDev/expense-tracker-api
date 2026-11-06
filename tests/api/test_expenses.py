from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient

EXPENSE = {
    "name": "Coffee",
    "category": "food",
    "amount": "4.50",
    "expense_date": "2026-01-15T10:30:00",
}


def _create(client: TestClient, headers: dict[str, str], **overrides: Any) -> dict[str, Any]:
    response = client.post("/api/v1/expenses/", json={**EXPENSE, **overrides}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_expense(client: TestClient, headers: dict[str, str]) -> None:
    body = _create(client, headers)

    assert body["name"] == "Coffee"
    assert body["category"] == "food"
    assert Decimal(body["amount"]) == Decimal("4.50")
    assert body["id"]


def test_create_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/v1/expenses/", json=EXPENSE).status_code == 401


def test_list_expenses_includes_only_own(
    client: TestClient,
    headers: dict[str, str],
    register_user: Any,
    login: Any,
) -> None:
    _create(client, headers, name="Mine")

    other = register_user(username="bob", email="bob@example.com")
    other_headers = login(other["email"])
    _create(client, other_headers, name="Theirs")

    response = client.get("/api/v1/expenses/", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [expense["name"] for expense in body["items"]] == ["Mine"]


def test_get_single_expense(client: TestClient, headers: dict[str, str]) -> None:
    created = _create(client, headers)

    response = client.get(f"/api/v1/expenses/{created['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_other_users_expense_returns_404(
    client: TestClient,
    headers: dict[str, str],
    register_user: Any,
    login: Any,
) -> None:
    created = _create(client, headers)

    other = register_user(username="bob", email="bob@example.com")
    other_headers = login(other["email"])

    assert client.get(f"/api/v1/expenses/{created['id']}", headers=other_headers).status_code == 404


def test_update_expense(client: TestClient, headers: dict[str, str]) -> None:
    created = _create(client, headers)

    response = client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"amount": "9.99", "category": "transport"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["amount"]) == Decimal("9.99")
    assert body["category"] == "transport"
    assert body["name"] == "Coffee"


def test_update_other_users_expense_returns_404(
    client: TestClient,
    headers: dict[str, str],
    register_user: Any,
    login: Any,
) -> None:
    created = _create(client, headers)

    other = register_user(username="bob", email="bob@example.com")
    other_headers = login(other["email"])

    response = client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"amount": "1.00"},
        headers=other_headers,
    )

    assert response.status_code == 404


def test_delete_expense(client: TestClient, headers: dict[str, str]) -> None:
    created = _create(client, headers)

    response = client.delete(f"/api/v1/expenses/{created['id']}", headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/v1/expenses/{created['id']}", headers=headers).status_code == 404


def test_delete_other_users_expense_returns_404(
    client: TestClient,
    headers: dict[str, str],
    register_user: Any,
    login: Any,
) -> None:
    created = _create(client, headers)

    other = register_user(username="bob", email="bob@example.com")
    other_headers = login(other["email"])

    assert (
        client.delete(f"/api/v1/expenses/{created['id']}", headers=other_headers).status_code == 404
    )


def test_expense_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/expenses/").status_code == 401
    assert client.get("/api/v1/expenses/1").status_code == 401
    assert client.patch("/api/v1/expenses/1", json={"amount": "1.00"}).status_code == 401
    assert client.delete("/api/v1/expenses/1").status_code == 401


def test_amount_must_be_positive(client: TestClient, headers: dict[str, str]) -> None:
    for amount in ("0", "-5.00"):
        response = client.post(
            "/api/v1/expenses/",
            json={**EXPENSE, "amount": amount},
            headers=headers,
        )
        assert response.status_code == 422


def test_amount_has_at_most_two_decimal_places(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/expenses/",
        json={**EXPENSE, "amount": "4.567"},
        headers=headers,
    )

    assert response.status_code == 422


def test_patch_can_clear_nullable_name(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    created = _create(client, headers)

    response = client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"name": None},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] is None


def test_patch_rejects_null_required_fields(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    created = _create(client, headers)

    for field in ("category", "amount", "expense_date"):
        response = client.patch(
            f"/api/v1/expenses/{created['id']}",
            json={field: None},
            headers=headers,
        )
        assert response.status_code == 422, field


def test_patch_with_empty_body_changes_nothing(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    created = _create(client, headers)

    response = client.patch(f"/api/v1/expenses/{created['id']}", json={}, headers=headers)

    assert response.status_code == 200
    assert response.json() == created


def test_patch_rejects_unknown_fields(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    created = _create(client, headers)

    response = client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"is_recurring": True},
        headers=headers,
    )

    assert response.status_code == 422


def test_create_rejects_unknown_fields(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/expenses/",
        json={**EXPENSE, "is_recurring": True},
        headers=headers,
    )

    assert response.status_code == 422


def _create_three(client: TestClient, headers: dict[str, str]) -> None:
    _create(
        client,
        headers,
        name="January",
        category="food",
        expense_date="2026-01-10T10:00:00",
    )
    _create(
        client,
        headers,
        name="February",
        category="transport",
        expense_date="2026-02-10T10:00:00",
    )
    _create(
        client,
        headers,
        name="March",
        category="food",
        expense_date="2026-03-10T10:00:00",
    )


def test_list_is_paginated(client: TestClient, headers: dict[str, str]) -> None:
    _create_three(client, headers)

    first_page = client.get("/api/v1/expenses/?limit=2", headers=headers)

    assert first_page.status_code == 200
    body = first_page.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert [expense["name"] for expense in body["items"]] == ["March", "February"]

    second_page = client.get("/api/v1/expenses/?limit=2&offset=2", headers=headers)

    assert second_page.status_code == 200
    body = second_page.json()
    assert body["total"] == 3
    assert body["offset"] == 2
    assert [expense["name"] for expense in body["items"]] == ["January"]


def test_list_filters_by_category(client: TestClient, headers: dict[str, str]) -> None:
    _create_three(client, headers)

    response = client.get("/api/v1/expenses/?category=food", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [expense["name"] for expense in body["items"]] == ["March", "January"]


def test_list_filters_by_date_range(client: TestClient, headers: dict[str, str]) -> None:
    _create_three(client, headers)

    response = client.get(
        "/api/v1/expenses/?start_date=2026-02-01T00:00:00&end_date=2026-02-28T23:59:59",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [expense["name"] for expense in body["items"]] == ["February"]


def test_list_rejects_inverted_date_range(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/expenses/?start_date=2026-03-01T00:00:00&end_date=2026-01-01T00:00:00",
        headers=headers,
    )

    assert response.status_code == 422


def test_list_validates_pagination_bounds(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    for query in ("limit=0", "limit=101", "offset=-1"):
        response = client.get(f"/api/v1/expenses/?{query}", headers=headers)
        assert response.status_code == 422, query


def test_list_supports_ascending_order(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    _create_three(client, headers)

    response = client.get("/api/v1/expenses/?order=asc", headers=headers)

    assert response.status_code == 200
    assert [expense["name"] for expense in response.json()["items"]] == [
        "January",
        "February",
        "March",
    ]


def test_list_rejects_invalid_order(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get("/api/v1/expenses/?order=sideways", headers=headers)

    assert response.status_code == 422


def test_list_returns_empty_page(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get("/api/v1/expenses/?category=missing", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}
