from packages.core.domain.entities import Cart, CartItem
from packages.core.domain.exceptions import ValidationError


def add_to_cart(*, cart: Cart, product_id: str, qty: int) -> Cart:
    if qty <= 0:
        msg = "qty must be greater than zero"
        raise ValidationError(msg)
    if not product_id.strip():
        msg = "product id cannot be empty"
        raise ValidationError(msg)

    for item in cart.items:
        if item.product_id == product_id:
            item.qty += qty
            return cart

    cart.items.append(CartItem(product_id=product_id, qty=qty))
    return cart
