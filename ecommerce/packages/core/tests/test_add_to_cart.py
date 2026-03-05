import pytest
from packages.core.application.use_cases import add_to_cart
from packages.core.domain.entities import Cart
from packages.core.domain.exceptions import ValidationError


def test_add_to_cart_adds_new_item() -> None:
    cart = Cart()

    updated = add_to_cart(cart=cart, product_id="p-1", qty=2)

    assert updated is cart
    assert len(updated.items) == 1
    assert updated.items[0].product_id == "p-1"
    assert updated.items[0].qty == 2


def test_add_to_cart_merges_existing_item_quantity() -> None:
    cart = Cart()
    add_to_cart(cart=cart, product_id="p-1", qty=2)

    updated = add_to_cart(cart=cart, product_id="p-1", qty=3)

    assert len(updated.items) == 1
    assert updated.items[0].qty == 5


def test_add_to_cart_rejects_invalid_qty() -> None:
    cart = Cart()

    with pytest.raises(ValidationError):
        add_to_cart(cart=cart, product_id="p-1", qty=0)
