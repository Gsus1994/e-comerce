from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import pytest
from packages.core.application.use_cases import add_to_cart, create_order, list_products
from packages.core.domain.entities import Cart, CartItem, Order, Product


class FakeProductRepository:
    def __init__(self, products: list[Product]) -> None:
        self._products = products

    def get_by_id(self, product_id: str) -> Product | None:
        return next((product for product in self._products if product.id == product_id), None)

    def list(self, *, page: int, size: int) -> tuple[Sequence[Product], int]:
        start = (page - 1) * size
        end = start + size
        return self._products[start:end], len(self._products)

    def search(self, *, query: str, page: int, size: int) -> tuple[Sequence[Product], int]:
        q = query.lower()
        filtered = [
            product
            for product in self._products
            if q in product.name.lower() or q in product.description.lower()
        ]
        start = (page - 1) * size
        end = start + size
        return filtered[start:end], len(filtered)


class FakeOrderRepository:
    def __init__(self) -> None:
        self.saved: list[Order] = []

    def create(self, order: Order) -> Order:
        self.saved.append(order)
        return order

    def list_by_user(self, user_id: str) -> list[Order]:
        return [order for order in self.saved if order.user_id == user_id]


def _products() -> list[Product]:
    return [
        Product(id="p-1", name="Phone", description="Smartphone", price=Decimal("100"), stock=10),
        Product(id="p-2", name="Case", description="Phone case", price=Decimal("10"), stock=100),
        Product(id="p-3", name="Cable", description="USB cable", price=Decimal("5"), stock=100),
        Product(id="p-4", name="Laptop", description="Ultrabook", price=Decimal("900"), stock=4),
    ]


@pytest.mark.parametrize(
    ("page", "size", "expected_count", "has_prev", "has_next"),
    [
        (1, 1, 1, False, True),
        (1, 2, 2, False, True),
        (1, 3, 3, False, True),
        (1, 4, 4, False, False),
        (2, 1, 1, True, True),
        (2, 2, 2, True, False),
        (2, 3, 1, True, False),
        (3, 1, 1, True, True),
        (3, 2, 0, True, False),
        (4, 1, 1, True, False),
        (5, 1, 0, True, False),
        (10, 1, 0, True, False),
    ],
)
def test_list_products_pagination_invariants(
    page: int,
    size: int,
    expected_count: int,
    has_prev: bool,
    has_next: bool,
) -> None:
    result = list_products(repository=FakeProductRepository(_products()), page=page, size=size)

    assert len(result["items"]) == expected_count
    assert result["meta"]["has_prev"] is has_prev
    assert result["meta"]["has_next"] is has_next


@pytest.mark.parametrize(
    ("query", "expected_total_items"),
    [
        ("phone", 2),
        ("PHONE", 2),
        (" laptop ", 1),
        ("usb", 1),
        ("missing", 0),
        ("", 4),
    ],
)
def test_list_products_query_invariants(query: str, expected_total_items: int) -> None:
    result = list_products(repository=FakeProductRepository(_products()), page=1, size=10, q=query)

    assert result["meta"]["total_items"] == expected_total_items
    assert result["meta"]["query"] == query.strip()


@pytest.mark.parametrize(
    "steps",
    [
        [("p-1", 1)],
        [("p-1", 1), ("p-1", 1)],
        [("p-1", 2), ("p-1", 3)],
        [("p-1", 1), ("p-2", 1)],
        [("p-2", 2), ("p-1", 1), ("p-2", 3)],
        [("p-1", 5), ("p-1", 4), ("p-1", 1)],
        [("p-3", 1), ("p-3", 2), ("p-3", 3)],
        [("p-4", 1), ("p-1", 1), ("p-4", 2)],
        [("p-2", 1), ("p-3", 1), ("p-2", 1), ("p-3", 1)],
        [("p-1", 10)],
    ],
)
def test_add_to_cart_preserves_merge_invariants(steps: list[tuple[str, int]]) -> None:
    cart = Cart()
    expected_qty: dict[str, int] = {}

    for product_id, qty in steps:
        add_to_cart(cart=cart, product_id=product_id, qty=qty)
        expected_qty[product_id] = expected_qty.get(product_id, 0) + qty

    assert {item.product_id: item.qty for item in cart.items} == expected_qty


@pytest.mark.parametrize(
    "items",
    [
        [CartItem(product_id="p-1", qty=1)],
        [CartItem(product_id="p-1", qty=2)],
        [CartItem(product_id="p-2", qty=3)],
        [CartItem(product_id="p-1", qty=1), CartItem(product_id="p-2", qty=2)],
        [CartItem(product_id="p-2", qty=2), CartItem(product_id="p-2", qty=3)],
        [CartItem(product_id="p-3", qty=5)],
        [CartItem(product_id="p-4", qty=1), CartItem(product_id="p-1", qty=1)],
        [CartItem(product_id="p-1", qty=1), CartItem(product_id="p-1", qty=1)],
    ],
)
def test_create_order_total_matches_sum_of_order_items(items: list[CartItem]) -> None:
    product_repository = FakeProductRepository(_products())
    order_repository = FakeOrderRepository()

    order = create_order(
        user_id="u-1",
        items=items,
        product_repository=product_repository,
        order_repository=order_repository,
    )

    reconstructed_total = sum(
        (item.unit_price * item.qty for item in order.items),
        start=Decimal("0"),
    )
    assert order.total == reconstructed_total
    assert order_repository.saved and order_repository.saved[0] is order
