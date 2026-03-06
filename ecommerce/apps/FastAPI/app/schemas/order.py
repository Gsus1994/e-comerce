from __future__ import annotations

from datetime import datetime

from packages.core.domain.entities import Order, OrderItem
from pydantic import BaseModel, Field


class CartItemRequest(BaseModel):
    product_id: str = Field(min_length=1)
    qty: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    items: list[CartItemRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    product_id: str
    qty: int
    unit_price: float

    @classmethod
    def from_entity(cls, item: OrderItem) -> OrderItemResponse:
        return cls(
            product_id=item.product_id,
            qty=item.qty,
            unit_price=float(item.unit_price),
        )


class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: list[OrderItemResponse]
    total: float
    status: str
    created_at: datetime

    @classmethod
    def from_entity(cls, order: Order) -> OrderResponse:
        return cls(
            id=order.id,
            user_id=order.user_id,
            items=[OrderItemResponse.from_entity(item) for item in order.items],
            total=float(order.total),
            status=order.status,
            created_at=order.created_at,
        )


class CartValidateRequest(BaseModel):
    items: list[CartItemRequest] = Field(min_length=1)


class CartValidationItem(BaseModel):
    product_id: str
    qty: int
    unit_price: float
    subtotal: float


class CartValidateResponse(BaseModel):
    items: list[CartValidationItem]
    total: float
