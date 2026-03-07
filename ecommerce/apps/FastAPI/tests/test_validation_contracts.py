from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "1234567"},
        {"email": "a@example.com"},
        {"password": "strongpass1"},
        {},
        {"email": 123, "password": "strongpass1"},
        {"email": "a@example.com", "password": 12345678},
        {"email": "a@example.com", "password": None},
    ],
)
def test_register_rejects_invalid_payloads(client: TestClient, payload: dict[str, object]) -> None:
    response = client.post("/v1/auth/register", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "1234567"},
        {"email": "a@example.com"},
        {"password": "strongpass1"},
        {},
        {"email": 123, "password": "strongpass1"},
        {"email": "a@example.com", "password": 12345678},
        {"email": "a@example.com", "password": None},
    ],
)
def test_login_rejects_invalid_payloads(client: TestClient, payload: dict[str, object]) -> None:
    response = client.post("/v1/auth/login", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "a@example.com", "new_password": "short"},
        {"email": "a@example.com", "new_password": "1234567"},
        {"email": "a@example.com"},
        {"new_password": "newstrongpass1"},
        {},
        {"email": 123, "new_password": "newstrongpass1"},
        {"email": "a@example.com", "new_password": 12345678},
        {"email": "a@example.com", "new_password": None},
    ],
)
def test_recover_password_rejects_invalid_payloads(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/v1/auth/recover-password", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("page", "size"),
    [
        (0, 20),
        (-1, 20),
        (1, 0),
        (1, -1),
        (1, 101),
        (1, 1000),
    ],
)
def test_list_products_rejects_invalid_query_params(
    client: TestClient,
    page: int,
    size: int,
) -> None:
    response = client.get("/v1/products", params={"page": page, "size": size})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"items": []},
        {"items": [{}]},
        {"items": [{"product_id": "p-1"}]},
        {"items": [{"qty": 1}]},
        {"items": [{"product_id": "p-1", "qty": 0}]},
        {"items": [{"product_id": "p-1", "qty": -1}]},
        {"items": [{"product_id": "p-1", "qty": "bad"}]},
    ],
)
def test_validate_cart_rejects_invalid_payloads(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/v1/cart/validate", json=payload)

    assert response.status_code == 422


def _register_user(client: TestClient, email: str) -> str:
    response = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "strongpass1"},
    )
    assert response.status_code == 201
    return str(response.json()["access_token"])


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"items": []},
        {"items": [{}]},
        {"items": [{"product_id": "p-1"}]},
        {"items": [{"qty": 1}]},
        {"items": [{"product_id": "p-1", "qty": 0}]},
        {"items": [{"product_id": "p-1", "qty": -1}]},
        {"items": [{"product_id": "p-1", "qty": "bad"}]},
    ],
)
def test_create_order_rejects_invalid_payloads_even_with_auth(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    token = _register_user(client, email=f"validation-orders-{uuid4().hex}@example.com")
    response = client.post(
        "/v1/orders",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "items_payload",
    [
        [{"product_id": "p-1", "qty": 1}],
        [{"product_id": "p-1", "qty": 2}, {"product_id": "p-1", "qty": 1}],
        [{"product_id": "p-1", "qty": 3}, {"product_id": "p-2", "qty": 1}],
        [{"product_id": "p-1", "qty": 1}, {"product_id": "p-2", "qty": 1}],
        [{"product_id": "p-3", "qty": 1}],
    ],
)
def test_validate_cart_accepts_payload_shape_with_positive_qty(
    client: TestClient,
    items_payload: list[dict[str, object]],
) -> None:
    response = client.post("/v1/cart/validate", json={"items": items_payload})

    # Puede devolver 200/404/409 según el catálogo existente; este contrato valida forma.
    assert response.status_code in {200, 404, 409}


@pytest.mark.parametrize(
    "query",
    ["", " ", "phone", "PHONE", "  phone  "],
)
def test_list_products_accepts_string_query_variants(client: TestClient, query: str) -> None:
    response = client.get("/v1/products", params={"page": 1, "size": 20, "q": query})

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert "meta" in payload


@pytest.mark.parametrize(
    "endpoint",
    ["/v1/orders", "/v1/orders/me"],
)
def test_orders_endpoints_require_authentication(client: TestClient, endpoint: str) -> None:
    if endpoint.endswith("/me"):
        response = client.get(endpoint)
    else:
        response = client.post(endpoint, json={"items": [{"product_id": "p-1", "qty": 1}]})

    assert response.status_code in {401, 403}
