from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from packages.core.domain.entities import CartItem, Order, OrderItem, Product, User
from packages.core.domain.exceptions import ValidationError


def test_product_normalizes_price_to_decimal() -> None:
    product = Product(
        id="p-1",
        name="Phone",
        description="Smartphone",
        price=cast(Decimal, 10),
        stock=5,
    )

    assert isinstance(product.price, Decimal)
    assert product.price == Decimal("10")


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: Product(
                id="",
                name="Phone",
                description="x",
                price=Decimal("1"),
                stock=1,
            ),
            "product id cannot be empty",
        ),
        (
            lambda: Product(
                id="p-1",
                name="",
                description="x",
                price=Decimal("1"),
                stock=1,
            ),
            "product name cannot be empty",
        ),
        (
            lambda: Product(
                id="p-1",
                name="Phone",
                description="x",
                price=Decimal("-1"),
                stock=1,
            ),
            "product price cannot be negative",
        ),
        (
            lambda: Product(
                id="p-1",
                name="Phone",
                description="x",
                price=Decimal("1"),
                stock=-1,
            ),
            "product stock cannot be negative",
        ),
    ],
)
def test_product_validation_errors(factory: Callable[[], object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        factory()


@pytest.mark.parametrize(
    ("product_id", "qty", "message"),
    [
        ("", 1, "product id cannot be empty"),
        ("p-1", 0, "qty must be greater than zero"),
    ],
)
def test_cart_item_validation_errors(product_id: str, qty: int, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        CartItem(product_id=product_id, qty=qty)


def test_order_item_normalizes_unit_price_to_decimal() -> None:
    item = OrderItem(product_id="p-1", qty=2, unit_price=cast(Decimal, 99))

    assert isinstance(item.unit_price, Decimal)
    assert item.unit_price == Decimal("99")


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: OrderItem(product_id="", qty=1, unit_price=Decimal("1")),
            "product id cannot be empty",
        ),
        (
            lambda: OrderItem(product_id="p-1", qty=0, unit_price=Decimal("1")),
            "qty must be greater than zero",
        ),
        (
            lambda: OrderItem(product_id="p-1", qty=1, unit_price=Decimal("-1")),
            "unit price cannot be negative",
        ),
    ],
)
def test_order_item_validation_errors(factory: Callable[[], object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        factory()


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: Order(
                id="",
                user_id="u-1",
                items=[OrderItem(product_id="p-1", qty=1, unit_price=Decimal("10"))],
                total=Decimal("10"),
                status="pending",
            ),
            "order id cannot be empty",
        ),
        (
            lambda: Order(
                id="o-1",
                user_id="",
                items=[OrderItem(product_id="p-1", qty=1, unit_price=Decimal("10"))],
                total=Decimal("10"),
                status="pending",
            ),
            "user id cannot be empty",
        ),
        (
            lambda: Order(
                id="o-1",
                user_id="u-1",
                items=[],
                total=Decimal("10"),
                status="pending",
            ),
            "order must contain at least one item",
        ),
        (
            lambda: Order(
                id="o-1",
                user_id="u-1",
                items=[OrderItem(product_id="p-1", qty=1, unit_price=Decimal("10"))],
                total=Decimal("-1"),
                status="pending",
            ),
            "order total cannot be negative",
        ),
        (
            lambda: Order(
                id="o-1",
                user_id="u-1",
                items=[OrderItem(product_id="p-1", qty=1, unit_price=Decimal("10"))],
                total=Decimal("10"),
                status="",
            ),
            "order status cannot be empty",
        ),
    ],
)
def test_order_validation_errors(factory: Callable[[], object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        factory()


def test_order_defaults_created_at_in_utc() -> None:
    order = Order(
        id="o-1",
        user_id="u-1",
        items=[OrderItem(product_id="p-1", qty=1, unit_price=Decimal("10"))],
        total=Decimal("10"),
        status="pending",
    )

    assert order.created_at.tzinfo == UTC
    assert order.created_at <= datetime.now(UTC)


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: User(id="", email="user@example.com", hashed_password="hashed"),
            "user id cannot be empty",
        ),
        (
            lambda: User(id="u-1", email="invalid", hashed_password="hashed"),
            "user email is invalid",
        ),
        (
            lambda: User(id="u-1", email="@example.com", hashed_password="hashed"),
            "user email is invalid",
        ),
        (
            lambda: User(id="u-1", email="user@example.com", hashed_password=""),
            "hashed password cannot be empty",
        ),
    ],
)
def test_user_validation_errors(factory: Callable[[], object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        factory()
