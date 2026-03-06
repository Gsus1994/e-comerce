from decimal import Decimal

from packages.core.infrastructure.db.models import ProductModel
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient


def _register_user(client: TestClient) -> str:
    response = client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass1"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_auth_register_and_login(client: TestClient) -> None:
    register_response = client.post(
        "/v1/auth/register",
        json={"email": "auth@example.com", "password": "strongpass1"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/v1/auth/login",
        json={"email": "auth@example.com", "password": "strongpass1"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
    assert login_response.json()["access_token"]


def test_auth_recover_password_updates_credentials(client: TestClient) -> None:
    register_response = client.post(
        "/v1/auth/register",
        json={"email": "recover@example.com", "password": "strongpass1"},
    )
    assert register_response.status_code == 201

    recover_response = client.post(
        "/v1/auth/recover-password",
        json={"email": "recover@example.com", "new_password": "newstrongpass1"},
    )
    assert recover_response.status_code == 200

    old_login_response = client.post(
        "/v1/auth/login",
        json={"email": "recover@example.com", "password": "strongpass1"},
    )
    assert old_login_response.status_code == 401

    new_login_response = client.post(
        "/v1/auth/login",
        json={"email": "recover@example.com", "password": "newstrongpass1"},
    )
    assert new_login_response.status_code == 200


def test_cart_validate_and_order_flow(client: TestClient, db_session: Session) -> None:
    db_session.add(
        ProductModel(
            id="p-1",
            name="Phone",
            description="Smartphone",
            price=Decimal("100.00"),
            stock=5,
        ),
    )
    db_session.commit()

    token = _register_user(client)
    auth_header = {"Authorization": f"Bearer {token}"}

    cart_response = client.post(
        "/v1/cart/validate",
        json={"items": [{"product_id": "p-1", "qty": 2}, {"product_id": "p-1", "qty": 1}]},
    )
    assert cart_response.status_code == 200
    assert cart_response.json()["items"][0]["qty"] == 3
    assert cart_response.json()["total"] == 300.0

    create_order_response = client.post(
        "/v1/orders",
        headers=auth_header,
        json={"items": [{"product_id": "p-1", "qty": 2}]},
    )
    assert create_order_response.status_code == 201
    order_payload = create_order_response.json()
    assert order_payload["status"] == "pending"
    assert order_payload["total"] == 200.0

    list_orders_response = client.get("/v1/orders/me", headers=auth_header)
    assert list_orders_response.status_code == 200
    orders_payload = list_orders_response.json()
    assert len(orders_payload) == 1
    assert orders_payload[0]["id"] == order_payload["id"]
