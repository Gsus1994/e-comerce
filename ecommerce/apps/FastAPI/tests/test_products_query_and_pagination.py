from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from packages.core.infrastructure.db.models import ProductModel


def test_list_products_trims_query_and_searches_name_and_description(
    client: TestClient, db_session: Session
) -> None:
    db_session.add_all(
        [
            ProductModel(
                id="p-1",
                name="Phone XL",
                description="Flagship device",
                price=Decimal("900.00"),
                stock=5,
            ),
            ProductModel(
                id="p-2",
                name="Cover",
                description="Phone protection case",
                price=Decimal("19.90"),
                stock=30,
            ),
            ProductModel(
                id="p-3",
                name="Keyboard",
                description="Mechanical keyboard",
                price=Decimal("80.00"),
                stock=8,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/v1/products", params={"q": "  phone  ", "page": 1, "size": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["query"] == "phone"
    assert payload["meta"]["total_items"] == 2
    assert [item["id"] for item in payload["items"]] == ["p-2", "p-1"]


def test_list_products_pagination_metadata_is_consistent(
    client: TestClient, db_session: Session
) -> None:
    db_session.add_all(
        [
            ProductModel(
                id="p-1",
                name="A",
                description="A product",
                price=Decimal("1.00"),
                stock=1,
            ),
            ProductModel(
                id="p-2",
                name="B",
                description="B product",
                price=Decimal("2.00"),
                stock=1,
            ),
            ProductModel(
                id="p-3",
                name="C",
                description="C product",
                price=Decimal("3.00"),
                stock=1,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/v1/products", params={"page": 2, "size": 2})

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == ["p-3"]
    assert payload["meta"] == {
        "page": 2,
        "size": 2,
        "total_items": 3,
        "total_pages": 2,
        "has_prev": True,
        "has_next": False,
        "query": "",
    }
