from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal

from packages.core.application.use_cases import create_order
from packages.core.domain.entities import CartItem, Order, Product


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


class RecordingOrderRepository:
    def __init__(self) -> None:
        self.create_calls = 0
        self.last_received_order: Order | None = None

    def create(self, order: Order) -> Order:
        self.create_calls += 1
        self.last_received_order = order
        return order

    def list_by_user(self, user_id: str) -> list[Order]:
        return []


class MappingOrderRepository(RecordingOrderRepository):
    def create(self, order: Order) -> Order:
        super().create(order)
        # Simula una capa de persistencia que ajusta estado antes de devolver.
        return replace(order, status="created")


def test_create_order_aggregates_items_preserving_first_seen_product_order() -> None:
    product_1 = Product(
        id="p-1",
        name="Phone",
        description="Smartphone",
        price=Decimal("100.00"),
        stock=10,
    )
    product_2 = Product(
        id="p-2",
        name="Case",
        description="Phone case",
        price=Decimal("9.99"),
        stock=10,
    )
    product_repository = FakeProductRepository([product_1, product_2])
    order_repository = RecordingOrderRepository()

    order = create_order(
        user_id="u-1",
        items=[
            CartItem(product_id="p-2", qty=1),
            CartItem(product_id="p-1", qty=2),
            CartItem(product_id="p-2", qty=3),
        ],
        product_repository=product_repository,
        order_repository=order_repository,
    )

    assert order_repository.create_calls == 1
    assert order_repository.last_received_order is order
    assert [(item.product_id, item.qty) for item in order.items] == [("p-2", 4), ("p-1", 2)]
    assert order.total == Decimal("239.96")


def test_create_order_returns_mapped_order_from_repository() -> None:
    product_repository = FakeProductRepository(
        [
            Product(
                id="p-1",
                name="Phone",
                description="Smartphone",
                price=Decimal("100.00"),
                stock=5,
            )
        ]
    )
    order_repository = MappingOrderRepository()

    created_order = create_order(
        user_id="u-1",
        items=[CartItem(product_id="p-1", qty=1)],
        product_repository=product_repository,
        order_repository=order_repository,
    )

    assert order_repository.create_calls == 1
    assert order_repository.last_received_order is not None
    assert order_repository.last_received_order.status == "pending"
    assert created_order.status == "created"
