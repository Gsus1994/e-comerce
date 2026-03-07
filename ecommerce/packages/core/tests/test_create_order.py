from collections.abc import Sequence
from decimal import Decimal

import pytest

from packages.core.application.use_cases import create_order
from packages.core.domain.entities import CartItem, Order, Product
from packages.core.domain.exceptions import NotFound, StockInsufficient


class FakeProductRepository:
    def __init__(self, products: list[Product]) -> None:
        self.products_by_id = {product.id: product for product in products}

    def get_by_id(self, product_id: str) -> Product | None:
        return self.products_by_id.get(product_id)

    def list(self, *, page: int, size: int) -> tuple[Sequence[Product], int]:
        products = list(self.products_by_id.values())
        start = (page - 1) * size
        end = start + size
        return products[start:end], len(products)

    def search(self, *, query: str, page: int, size: int) -> tuple[Sequence[Product], int]:
        products = [
            product
            for product in self.products_by_id.values()
            if query.lower() in product.name.lower() or query.lower() in product.description.lower()
        ]
        start = (page - 1) * size
        end = start + size
        return products[start:end], len(products)


class FakeOrderRepository:
    def __init__(self) -> None:
        self.saved_orders: list[Order] = []

    def create(self, order: Order) -> Order:
        self.saved_orders.append(order)
        return order

    def list_by_user(self, user_id: str) -> list[Order]:
        return [order for order in self.saved_orders if order.user_id == user_id]


def test_create_order_validates_stock_and_calculates_total() -> None:
    phone = Product(id="p-1", name="Phone", description="Smartphone", price=Decimal("100"), stock=5)
    case = Product(id="p-2", name="Case", description="Phone case", price=Decimal("10"), stock=10)
    product_repo = FakeProductRepository([phone, case])
    order_repo = FakeOrderRepository()

    order = create_order(
        user_id="u-1",
        items=[
            CartItem(product_id="p-1", qty=2),
            CartItem(product_id="p-2", qty=1),
            CartItem(product_id="p-1", qty=1),
        ],
        product_repository=product_repo,
        order_repository=order_repo,
    )

    assert len(order_repo.saved_orders) == 1
    assert order.id
    assert order.user_id == "u-1"
    assert order.status == "pending"
    assert len(order.items) == 2
    assert order.total == Decimal("310")
    assert phone.stock == 5
    assert case.stock == 10


def test_create_order_raises_when_product_not_found() -> None:
    product_repo = FakeProductRepository([])
    order_repo = FakeOrderRepository()

    with pytest.raises(NotFound):
        create_order(
            user_id="u-1",
            items=[CartItem(product_id="missing", qty=1)],
            product_repository=product_repo,
            order_repository=order_repo,
        )


def test_create_order_raises_when_stock_is_insufficient() -> None:
    phone = Product(id="p-1", name="Phone", description="Smartphone", price=Decimal("100"), stock=1)
    product_repo = FakeProductRepository([phone])
    order_repo = FakeOrderRepository()

    with pytest.raises(StockInsufficient):
        create_order(
            user_id="u-1",
            items=[CartItem(product_id="p-1", qty=2)],
            product_repository=product_repo,
            order_repository=order_repo,
        )
