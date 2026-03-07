from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

import pytest

from packages.core.application.use_cases import add_to_cart, create_order, list_products
from packages.core.domain.entities import Cart, CartItem, Order, Product
from packages.core.domain.exceptions import ValidationError


class FakeProductRepository:
    def __init__(self, products: list[Product]) -> None:
        self._products = products
        self.search_queries: list[str] = []

    def get_by_id(self, product_id: str) -> Product | None:
        return next((product for product in self._products if product.id == product_id), None)

    def list(self, *, page: int, size: int) -> tuple[Sequence[Product], int]:
        start = (page - 1) * size
        end = start + size
        return self._products[start:end], len(self._products)

    def search(self, *, query: str, page: int, size: int) -> tuple[Sequence[Product], int]:
        self.search_queries.append(query)
        filtered = [
            product
            for product in self._products
            if query.lower() in product.name.lower() or query.lower() in product.description.lower()
        ]
        start = (page - 1) * size
        end = start + size
        return filtered[start:end], len(filtered)


class FakeOrderRepository:
    def __init__(self) -> None:
        self.created_orders: list[Order] = []

    def create(self, order: Order) -> Order:
        self.created_orders.append(order)
        return order

    def list_by_user(self, user_id: str) -> list[Order]:
        return [order for order in self.created_orders if order.user_id == user_id]


def _products() -> list[Product]:
    return [
        Product(id="p-1", name="Phone", description="Smartphone", price=Decimal("100"), stock=5),
        Product(id="p-2", name="Case", description="Phone case", price=Decimal("10"), stock=10),
    ]


@pytest.mark.parametrize(("page", "size"), [(0, 10), (-1, 10), (1, 0), (1, -1)])
def test_list_products_rejects_non_positive_pagination(page: int, size: int) -> None:
    repository = FakeProductRepository(_products())

    with pytest.raises(ValidationError):
        list_products(repository=repository, page=page, size=size)


def test_list_products_trims_query_before_search() -> None:
    repository = FakeProductRepository(_products())

    result = list_products(repository=repository, page=1, size=10, q="  phone  ")

    assert repository.search_queries == ["phone"]
    assert result["meta"]["query"] == "phone"


def test_list_products_returns_zero_total_pages_when_empty() -> None:
    repository = FakeProductRepository([])

    result = list_products(repository=repository, page=1, size=20)

    assert result["items"] == []
    assert result["meta"]["total_items"] == 0
    assert result["meta"]["total_pages"] == 0
    assert result["meta"]["has_next"] is False


@pytest.mark.parametrize(("product_id", "qty"), [("", 1), ("   ", 1), ("p-1", -1)])
def test_add_to_cart_rejects_invalid_inputs(product_id: str, qty: int) -> None:
    cart = Cart()

    with pytest.raises(ValidationError):
        add_to_cart(cart=cart, product_id=product_id, qty=qty)


def test_create_order_rejects_empty_user_id() -> None:
    repository = FakeProductRepository(_products())
    order_repository = FakeOrderRepository()

    with pytest.raises(ValidationError, match="user id cannot be empty"):
        create_order(
            user_id="   ",
            items=[CartItem(product_id="p-1", qty=1)],
            product_repository=repository,
            order_repository=order_repository,
        )


def test_create_order_rejects_empty_items() -> None:
    repository = FakeProductRepository(_products())
    order_repository = FakeOrderRepository()

    with pytest.raises(ValidationError, match="order items cannot be empty"):
        create_order(
            user_id="u-1",
            items=[],
            product_repository=repository,
            order_repository=order_repository,
        )


@dataclass(slots=True)
class FakeCartItem:
    product_id: str
    qty: int


def test_create_order_rejects_items_with_non_positive_qty() -> None:
    repository = FakeProductRepository(_products())
    order_repository = FakeOrderRepository()
    invalid_items = cast(Sequence[CartItem], [FakeCartItem(product_id="p-1", qty=0)])

    with pytest.raises(ValidationError, match="qty must be greater than zero"):
        create_order(
            user_id="u-1",
            items=invalid_items,
            product_repository=repository,
            order_repository=order_repository,
        )
