from __future__ import annotations

from collections.abc import Sequence

from packages.core.application.ports import ProductRepository
from packages.core.domain.entities import Product
from packages.core.infrastructure.db.models import ProductModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session


class ProductSqlAlchemyRepository(ProductRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, product_id: str) -> Product | None:
        model = self._session.get(ProductModel, product_id)
        if model is None:
            return None
        return self._to_domain(model)

    def list(self, *, page: int, size: int) -> tuple[Sequence[Product], int]:
        offset = max(page - 1, 0) * size

        total_items = self._session.scalar(select(func.count()).select_from(ProductModel)) or 0
        statement = (
            select(ProductModel).order_by(ProductModel.name.asc()).offset(offset).limit(size)
        )
        rows = self._session.scalars(statement).all()
        return [self._to_domain(row) for row in rows], int(total_items)

    def search(self, *, query: str, page: int, size: int) -> tuple[Sequence[Product], int]:
        offset = max(page - 1, 0) * size
        pattern = f"%{query.strip()}%"
        filters = or_(ProductModel.name.ilike(pattern), ProductModel.description.ilike(pattern))

        total_statement = select(func.count()).select_from(ProductModel).where(filters)
        total_items = self._session.scalar(total_statement) or 0

        statement = (
            select(ProductModel)
            .where(filters)
            .order_by(ProductModel.name.asc())
            .offset(offset)
            .limit(size)
        )
        rows = self._session.scalars(statement).all()
        return [self._to_domain(row) for row in rows], int(total_items)

    @staticmethod
    def _to_domain(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            description=model.description,
            price=model.price,
            stock=model.stock,
        )
