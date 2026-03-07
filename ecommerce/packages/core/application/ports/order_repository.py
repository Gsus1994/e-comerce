from __future__ import annotations

from typing import Protocol

from packages.core.domain.entities import Order


class OrderRepository(Protocol):
    def create(self, order: Order) -> Order: ...

    def list_by_user(self, user_id: str) -> list[Order]: ...
