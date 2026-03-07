from collections.abc import Sequence
from decimal import Decimal

from packages.core.application.use_cases import list_products
from packages.core.domain.entities import Product


class FakeProductRepository:
    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self.last_called: str | None = None

    def get_by_id(self, product_id: str) -> Product | None:
        return next((p for p in self.products if p.id == product_id), None)

    def list(self, *, page: int, size: int) -> tuple[Sequence[Product], int]:
        self.last_called = "list"
        start = (page - 1) * size
        end = start + size
        return self.products[start:end], len(self.products)

    def search(self, *, query: str, page: int, size: int) -> tuple[Sequence[Product], int]:
        self.last_called = "search"
        q = query.lower()
        filtered = [p for p in self.products if q in p.name.lower() or q in p.description.lower()]
        start = (page - 1) * size
        end = start + size
        return filtered[start:end], len(filtered)


def _seed_products() -> list[Product]:
    return [
        Product(id="p-1", name="Phone", description="Smartphone", price=Decimal("100"), stock=10),
        Product(id="p-2", name="Case", description="Phone case", price=Decimal("10"), stock=50),
        Product(id="p-3", name="Laptop", description="Ultrabook", price=Decimal("900"), stock=5),
    ]


def test_list_products_returns_items_and_pagination_meta() -> None:
    repo = FakeProductRepository(_seed_products())

    result = list_products(repository=repo, page=1, size=2)

    assert repo.last_called == "list"
    assert [product.id for product in result["items"]] == ["p-1", "p-2"]
    assert result["meta"] == {
        "page": 1,
        "size": 2,
        "total_items": 3,
        "total_pages": 2,
        "has_prev": False,
        "has_next": True,
        "query": "",
    }


def test_list_products_uses_search_when_query_is_present() -> None:
    repo = FakeProductRepository(_seed_products())

    result = list_products(repository=repo, page=1, size=10, q="phone")

    assert repo.last_called == "search"
    assert [product.id for product in result["items"]] == ["p-1", "p-2"]
    assert result["meta"]["total_items"] == 2
