from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from packages.core.application.ports import OrderRepository
from packages.core.domain.entities import Order, OrderItem
from packages.core.infrastructure.db.models import OrderItemModel, OrderModel


class OrderSqlAlchemyRepository(OrderRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, order: Order) -> Order:
        order_model = OrderModel(
            id=order.id,
            user_id=order.user_id,
            total=order.total,
            status=order.status,
            created_at=order.created_at,
        )
        order_model.items = [
            OrderItemModel(
                product_id=item.product_id,
                qty=item.qty,
                unit_price=item.unit_price,
            )
            for item in order.items
        ]

        self._session.add(order_model)
        self._session.flush()

        return self._to_domain(order_model)

    def list_by_user(self, user_id: str) -> list[Order]:
        statement = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
        )
        rows = self._session.scalars(statement).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(model: OrderModel) -> Order:
        items = [
            OrderItem(
                product_id=item.product_id,
                qty=item.qty,
                unit_price=item.unit_price,
            )
            for item in model.items
        ]

        return Order(
            id=model.id,
            user_id=model.user_id,
            items=items,
            total=model.total,
            status=model.status,
            created_at=model.created_at,
        )
