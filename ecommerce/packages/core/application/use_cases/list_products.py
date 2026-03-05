from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from packages.core.application.ports import ProductRepository
from packages.core.domain.entities import Product
from packages.core.domain.exceptions import ValidationError


def list_products(
    *,
    repository: ProductRepository,
    page: int = 1,
    size: int = 20,
    q: str | None = None,
) -> dict[str, Any]:
    if page <= 0:
        msg = "page must be greater than zero"
        raise ValidationError(msg)
    if size <= 0:
        msg = "size must be greater than zero"
        raise ValidationError(msg)

    query = (q or "").strip()
    items: Sequence[Product]
    total_items: int

    if query:
        items, total_items = repository.search(query=query, page=page, size=size)
    else:
        items, total_items = repository.list(page=page, size=size)

    total_pages = (total_items + size - 1) // size if total_items > 0 else 0

    return {
        "items": list(items),
        "meta": {
            "page": page,
            "size": size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "query": query,
        },
    }
