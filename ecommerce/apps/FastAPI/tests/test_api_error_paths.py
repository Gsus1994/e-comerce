from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.FastAPI.app.deps import get_current_user
from apps.FastAPI.app.main import app
from packages.core.infrastructure.db.models import ProductModel


def _register_user(client: TestClient, email: str = "user@example.com") -> str:
    response = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "strongpass1"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    _ = _register_user(client, email="duplicate@example.com")

    second_response = client.post(
        "/v1/auth/register",
        json={"email": "DUPLICATE@example.com", "password": "strongpass1"},
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    _ = _register_user(client, email="login@example.com")

    response = client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "wrongpass1"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_cart_validate_returns_not_found_for_unknown_product(client: TestClient) -> None:
    response = client.post(
        "/v1/cart/validate",
        json={"items": [{"product_id": "missing", "qty": 1}]},
    )

    assert response.status_code == 404


def test_cart_validate_returns_conflict_for_insufficient_stock(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        ProductModel(
            id="p-1",
            name="Phone",
            description="Smartphone",
            price=Decimal("100.00"),
            stock=1,
        )
    )
    db_session.commit()

    response = client.post(
        "/v1/cart/validate",
        json={"items": [{"product_id": "p-1", "qty": 2}]},
    )

    assert response.status_code == 409


def test_cart_validate_returns_bad_request_for_blank_product_id(client: TestClient) -> None:
    response = client.post(
        "/v1/cart/validate",
        json={"items": [{"product_id": "   ", "qty": 1}]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "product id cannot be empty"


def test_create_order_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/v1/orders",
        json={"items": [{"product_id": "p-1", "qty": 1}]},
    )

    assert response.status_code == 401


def test_create_order_returns_not_found_for_unknown_product(client: TestClient) -> None:
    token = _register_user(client, email="order-missing@example.com")

    response = client.post(
        "/v1/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": "missing", "qty": 1}]},
    )

    assert response.status_code == 404


def test_create_order_returns_conflict_for_insufficient_stock(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        ProductModel(
            id="p-1",
            name="Phone",
            description="Smartphone",
            price=Decimal("100.00"),
            stock=1,
        )
    )
    db_session.commit()

    token = _register_user(client, email="order-stock@example.com")
    response = client.post(
        "/v1/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": "p-1", "qty": 2}]},
    )

    assert response.status_code == 409


def test_create_order_returns_bad_request_for_invalid_current_user_id(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        ProductModel(
            id="p-1",
            name="Phone",
            description="Smartphone",
            price=Decimal("100.00"),
            stock=5,
        )
    )
    db_session.commit()

    def _fake_current_user() -> SimpleNamespace:
        return SimpleNamespace(id="   ")

    app.dependency_overrides[get_current_user] = _fake_current_user
    try:
        response = client.post(
            "/v1/orders",
            json={"items": [{"product_id": "p-1", "qty": 1}]},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 400
    assert response.json()["detail"] == "user id cannot be empty"


def test_list_my_orders_rejects_invalid_token(client: TestClient) -> None:
    response = client.get("/v1/orders/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
