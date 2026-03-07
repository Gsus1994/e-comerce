from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from packages.core.domain.exceptions import ValidationError


@dataclass(slots=True)
class Product:
    id: str
    name: str
    description: str
    price: Decimal
    stock: int

    def __post_init__(self) -> None:
        if not self.id.strip():
            msg = "product id cannot be empty"
            raise ValidationError(msg)
        if not self.name.strip():
            msg = "product name cannot be empty"
            raise ValidationError(msg)
        self.price = Decimal(str(self.price))
        if self.price < 0:
            msg = "product price cannot be negative"
            raise ValidationError(msg)
        if self.stock < 0:
            msg = "product stock cannot be negative"
            raise ValidationError(msg)
