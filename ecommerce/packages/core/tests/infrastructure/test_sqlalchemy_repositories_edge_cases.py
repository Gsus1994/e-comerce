from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from packages.core.infrastructure.db.models import (
    Base,
    OrderItemModel,
    OrderModel,
    ProductModel,
    UserModel,
)
from packages.core.infrastructure.repositories import (
    OrderSqlAlchemyRepository,
    ProductSqlAlchemyRepository,
)


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    local_session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return local_session()


def test_product_repository_paginates_and_returns_none_for_missing_id() -> None:
    session = _session()
    try:
        session.add_all(
            [
                ProductModel(
                    id="p-1",
                    name="A",
                    description="first",
                    price=Decimal("10.00"),
                    stock=1,
                ),
                ProductModel(
                    id="p-2",
                    name="B",
                    description="second",
                    price=Decimal("20.00"),
                    stock=1,
                ),
                ProductModel(
                    id="p-3",
                    name="C",
                    description="third",
                    price=Decimal("30.00"),
                    stock=1,
                ),
            ],
        )
        session.commit()

        repository = ProductSqlAlchemyRepository(session)

        assert repository.get_by_id("missing") is None
        page_2_items, total = repository.list(page=2, size=2)

        assert total == 3
        assert [item.id for item in page_2_items] == ["p-3"]
    finally:
        session.close()


def test_product_repository_search_trims_query() -> None:
    session = _session()
    try:
        session.add_all(
            [
                ProductModel(
                    id="p-1",
                    name="Gaming Laptop",
                    description="High performance laptop",
                    price=Decimal("1000.00"),
                    stock=2,
                ),
                ProductModel(
                    id="p-2",
                    name="Office Chair",
                    description="Ergonomic",
                    price=Decimal("200.00"),
                    stock=5,
                ),
            ],
        )
        session.commit()

        repository = ProductSqlAlchemyRepository(session)
        results, total = repository.search(query="  laptop  ", page=1, size=10)

        assert total == 1
        assert [product.id for product in results] == ["p-1"]
    finally:
        session.close()


def test_order_repository_list_by_user_is_filtered_and_sorted_desc() -> None:
    session = _session()
    now = datetime.now(UTC)
    try:
        session.add_all(
            [
                UserModel(id="u-1", email="user1@example.com", hashed_password="x", is_admin=False),
                UserModel(id="u-2", email="user2@example.com", hashed_password="x", is_admin=False),
                ProductModel(
                    id="p-1",
                    name="Phone",
                    description="Smartphone",
                    price=Decimal("100.00"),
                    stock=10,
                ),
            ],
        )
        session.commit()

        old_order = OrderModel(
            id="o-old",
            user_id="u-1",
            total=Decimal("100.00"),
            status="pending",
            created_at=now - timedelta(days=1),
            items=[OrderItemModel(product_id="p-1", qty=1, unit_price=Decimal("100.00"))],
        )
        new_order = OrderModel(
            id="o-new",
            user_id="u-1",
            total=Decimal("200.00"),
            status="pending",
            created_at=now,
            items=[OrderItemModel(product_id="p-1", qty=2, unit_price=Decimal("100.00"))],
        )
        other_user_order = OrderModel(
            id="o-other",
            user_id="u-2",
            total=Decimal("100.00"),
            status="pending",
            created_at=now + timedelta(minutes=1),
            items=[OrderItemModel(product_id="p-1", qty=1, unit_price=Decimal("100.00"))],
        )

        session.add_all([old_order, new_order, other_user_order])
        session.commit()

        repository = OrderSqlAlchemyRepository(session)
        user_orders = repository.list_by_user("u-1")

        assert [order.id for order in user_orders] == ["o-new", "o-old"]
    finally:
        session.close()
