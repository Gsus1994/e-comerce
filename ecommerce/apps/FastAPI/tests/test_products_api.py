from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from packages.core.infrastructure.db.models import ProductModel


def test_list_products_returns_paginated_items(client: TestClient, db_session: Session) -> None:
    db_session.add_all(
        [
            ProductModel(
                id="p-1",
                name="Case",
                description="Phone case",
                price=Decimal("10.00"),
                stock=20,
            ),
            ProductModel(
                id="p-2",
                name="Phone",
                description="Smartphone",
                price=Decimal("100.00"),
                stock=5,
            ),
        ],
    )
    db_session.commit()

    response = client.get("/v1/products", params={"page": 1, "size": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_items"] == 2
    assert [item["id"] for item in payload["items"]] == ["p-1", "p-2"]


def test_get_product_by_id_returns_not_found_for_unknown_id(client: TestClient) -> None:
    response = client.get("/v1/products/unknown")

    assert response.status_code == 404


def test_get_product_by_id_returns_product(client: TestClient, db_session: Session) -> None:
    db_session.add(
        ProductModel(
            id="p-3",
            name="Keyboard",
            description="Mechanical keyboard",
            price=Decimal("80.00"),
            stock=8,
        )
    )
    db_session.commit()

    response = client.get("/v1/products/p-3")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "p-3"
    assert payload["name"] == "Keyboard"
