from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from packages.core.domain.entities import Order, OrderItem
from packages.core.infrastructure.db.models import Base, ProductModel, UserModel
from packages.core.infrastructure.repositories import (
    OrderSqlAlchemyRepository,
    ProductSqlAlchemyRepository,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    local_session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    return local_session()


def test_product_repository_list_search_and_get() -> None:
    session = _session()
    try:
        session.add_all(
            [
                ProductModel(
                    id="p-1",
                    name="Case",
                    description="Phone case",
                    price=Decimal("10.00"),
                    stock=20,
                ),
                ProductModel(
                    id="p-2",
                    name="Phone",
                    description="Smartphone",
                    price=Decimal("100.00"),
                    stock=5,
                ),
            ],
        )
        session.commit()

        repository = ProductSqlAlchemyRepository(session)

        found = repository.get_by_id("p-2")
        assert found is not None
        assert found.name == "Phone"

        products, total = repository.list(page=1, size=10)
        assert total == 2
        assert [product.id for product in products] == ["p-1", "p-2"]

        results, searched_total = repository.search(query="phone", page=1, size=10)
        assert searched_total == 2
        assert {product.id for product in results} == {"p-1", "p-2"}
    finally:
        session.close()


def test_order_repository_create_and_list_by_user() -> None:
    session = _session()
    try:
        session.add(
            UserModel(
                id="u-1",
                email="user@example.com",
                hashed_password="hashed",
                is_admin=False,
            ),
        )
        session.add(
            ProductModel(
                id="p-1",
                name="Phone",
                description="Smartphone",
                price=Decimal("100.00"),
                stock=5,
            ),
        )
        session.commit()

        repository = OrderSqlAlchemyRepository(session)
        order = Order(
            id="o-1",
            user_id="u-1",
            items=[OrderItem(product_id="p-1", qty=2, unit_price=Decimal("100.00"))],
            total=Decimal("200.00"),
            status="pending",
            created_at=datetime.now(UTC),
        )

        created = repository.create(order)
        session.commit()

        assert created.id == "o-1"
        assert created.total == Decimal("200.00")
        assert len(created.items) == 1

        by_user = repository.list_by_user("u-1")
        assert len(by_user) == 1
        assert by_user[0].id == "o-1"
        assert by_user[0].items[0].product_id == "p-1"
    finally:
        session.close()
