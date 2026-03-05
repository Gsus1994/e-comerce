from dataclasses import dataclass, field

from packages.core.domain.exceptions import ValidationError


@dataclass(slots=True)
class CartItem:
    product_id: str
    qty: int

    def __post_init__(self) -> None:
        if not self.product_id.strip():
            msg = "product id cannot be empty"
            raise ValidationError(msg)
        if self.qty <= 0:
            msg = "qty must be greater than zero"
            raise ValidationError(msg)


@dataclass(slots=True)
class Cart:
    items: list[CartItem] = field(default_factory=list)
