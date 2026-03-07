from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from packages.core.application.ports import OrderRepository, ProductRepository
from packages.core.domain.entities import CartItem, Order, OrderItem
from packages.core.domain.exceptions import NotFound, StockInsufficient, ValidationError


def create_order(
    *,
    user_id: str,
    items: Sequence[CartItem],
    product_repository: ProductRepository,
    order_repository: OrderRepository,
) -> Order:
    if not user_id.strip():
        msg = "user id cannot be empty"
        raise ValidationError(msg)
    if not items:
        msg = "order items cannot be empty"
        raise ValidationError(msg)

    aggregated_items: dict[str, int] = {}
    for item in items:
        if item.qty <= 0:
            msg = "qty must be greater than zero"
            raise ValidationError(msg)
        aggregated_items[item.product_id] = aggregated_items.get(item.product_id, 0) + item.qty

    order_items: list[OrderItem] = []
    total = Decimal("0")

    for product_id, qty in aggregated_items.items():
        product = product_repository.get_by_id(product_id)
        if product is None:
            msg = f"product '{product_id}' not found"
            raise NotFound(msg)
        if product.stock < qty:
            msg = f"insufficient stock for product '{product_id}'"
            raise StockInsufficient(msg)

        order_items.append(
            OrderItem(product_id=product.id, qty=qty, unit_price=product.price),
        )
        total += product.price * qty

    order = Order(
        id=str(uuid4()),
        user_id=user_id,
        items=order_items,
        total=total,
        status="pending",
        created_at=datetime.now(UTC),
    )

    return order_repository.create(order)
