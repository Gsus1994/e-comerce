from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from packages.core.domain.exceptions import ValidationError


@dataclass(slots=True)
class OrderItem:
    product_id: str
    qty: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if not self.product_id.strip():
            msg = "product id cannot be empty"
            raise ValidationError(msg)
        if self.qty <= 0:
            msg = "qty must be greater than zero"
            raise ValidationError(msg)
        self.unit_price = Decimal(str(self.unit_price))
        if self.unit_price < 0:
            msg = "unit price cannot be negative"
            raise ValidationError(msg)


@dataclass(slots=True)
class Order:
    id: str
    user_id: str
    items: list[OrderItem]
    total: Decimal
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.id.strip():
            msg = "order id cannot be empty"
            raise ValidationError(msg)
        if not self.user_id.strip():
            msg = "user id cannot be empty"
            raise ValidationError(msg)
        if not self.items:
            msg = "order must contain at least one item"
            raise ValidationError(msg)
        self.total = Decimal(str(self.total))
        if self.total < 0:
            msg = "order total cannot be negative"
            raise ValidationError(msg)
        if not self.status.strip():
            msg = "order status cannot be empty"
            raise ValidationError(msg)
