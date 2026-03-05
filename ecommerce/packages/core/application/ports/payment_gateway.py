from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class PaymentGateway(Protocol):
    """Stub port for future payment integration."""

    def charge(self, *, user_id: str, amount: Decimal, currency: str = "USD") -> str: ...
