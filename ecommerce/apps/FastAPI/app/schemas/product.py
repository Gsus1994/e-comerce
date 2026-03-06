from __future__ import annotations

from packages.core.domain.entities import Product
from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int

    @classmethod
    def from_entity(cls, product: Product) -> ProductResponse:
        return cls(
            id=product.id,
            name=product.name,
            description=product.description,
            price=float(product.price),
            stock=product.stock,
        )


class ProductPaginationMeta(BaseModel):
    page: int
    size: int
    total_items: int
    total_pages: int
    has_prev: bool
    has_next: bool
    query: str


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    meta: ProductPaginationMeta
