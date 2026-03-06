from __future__ import annotations

from decimal import Decimal
from typing import cast

import pytest
from packages.core.domain.entities import CartItem, Order, OrderItem, Product, User


@pytest.mark.parametrize(
    "price_input",
    [
        cast(Decimal, 0),
        cast(Decimal, 1),
        cast(Decimal, 10),
        Decimal("0"),
        Decimal("0.01"),
        Decimal("1.00"),
        Decimal("10.25"),
        Decimal("999.99"),
        Decimal("123456.78"),
        Decimal("5.5"),
    ],
)
def test_product_accepts_multiple_non_negative_price_values(price_input: Decimal) -> None:
    product = Product(
        id="p-1",
        name="Phone",
        description="Smartphone",
        price=price_input,
        stock=1,
    )

    assert product.price == Decimal(str(price_input))


@pytest.mark.parametrize(
    "stock",
    [0, 1, 2, 5, 10, 50, 100, 999, 10000],
)
def test_product_accepts_multiple_non_negative_stock_values(stock: int) -> None:
    product = Product(
        id="p-1",
        name="Phone",
        description="Smartphone",
        price=Decimal("1"),
        stock=stock,
    )

    assert product.stock == stock


@pytest.mark.parametrize(
    "email",
    [
        "u@example.com",
        "user.name@example.com",
        "user_name@example.com",
        "user-name@example.com",
        "user+alias@example.com",
        "user@sub.example.com",
        "a@b.co",
        "UPPER@EXAMPLE.COM",
        "mixed.Case+1@sub-domain.example",
        "x@y.z",
        "first.last@domain.io",
        "dev-team+alerts@company.org",
    ],
)
def test_user_accepts_valid_email_variants(email: str) -> None:
    user = User(id="u-1", email=email, hashed_password="hashed")

    assert user.email == email


@pytest.mark.parametrize("qty", [1, 2, 3, 5, 10, 99, 1000, 5000, 99999])
def test_cart_item_accepts_positive_quantities(qty: int) -> None:
    item = CartItem(product_id="p-1", qty=qty)

    assert item.qty == qty


@pytest.mark.parametrize(
    ("qty", "unit_price"),
    [
        (1, cast(Decimal, 0)),
        (1, cast(Decimal, 1)),
        (1, cast(Decimal, 10)),
        (2, Decimal("0.01")),
        (2, Decimal("1.25")),
        (2, Decimal("99.99")),
        (3, Decimal("1000.00")),
        (5, Decimal("7.50")),
        (8, Decimal("12.34")),
        (13, Decimal("0.10")),
        (21, Decimal("4.56")),
        (34, Decimal("9999.99")),
    ],
)
def test_order_item_accepts_positive_qty_and_non_negative_price(
    qty: int,
    unit_price: Decimal,
) -> None:
    item = OrderItem(product_id="p-1", qty=qty, unit_price=unit_price)

    assert item.qty == qty
    assert item.unit_price == Decimal(str(unit_price))


@pytest.mark.parametrize(
    "status",
    ["pending", "created", "paid", "processing", "shipped", "delivered", "cancelled", "x"],
)
def test_order_accepts_non_empty_status_values(status: str) -> None:
    order = Order(
        id="o-1",
        user_id="u-1",
        items=[OrderItem(product_id="p-1", qty=1, unit_price=Decimal("10"))],
        total=Decimal("10"),
        status=status,
    )

    assert order.status == status
