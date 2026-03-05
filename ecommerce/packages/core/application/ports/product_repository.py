from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from packages.core.domain.entities import Product


class ProductRepository(Protocol):
    def get_by_id(self, product_id: str) -> Product | None: ...

    def list(self, *, page: int, size: int) -> tuple[Sequence[Product], int]:
        """Return (items, total_items)."""

    def search(self, *, query: str, page: int, size: int) -> tuple[Sequence[Product], int]:
        """Return (items, total_items) filtered by query."""
