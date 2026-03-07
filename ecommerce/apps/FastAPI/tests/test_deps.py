from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from apps.FastAPI.app import deps
from packages.core.infrastructure.db.models import UserModel
from packages.core.infrastructure.repositories import (
    OrderSqlAlchemyRepository,
    ProductSqlAlchemyRepository,
)


@dataclass(slots=True)
class _FakeSession:
    closed: bool = False

    def close(self) -> None:
        self.closed = True


def test_get_session_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = _FakeSession()
    monkeypatch.setattr(deps, "SessionLocal", lambda: fake_session)

    session_generator = deps.get_session()
    session = next(session_generator)

    assert session is fake_session

    with pytest.raises(StopIteration):
        next(session_generator)

    assert fake_session.closed is True


def test_get_product_and_order_repositories(db_session: Session) -> None:
    product_repo = deps.get_product_repo(db_session)
    order_repo = deps.get_order_repo(db_session)

    assert isinstance(product_repo, ProductSqlAlchemyRepository)
    assert isinstance(order_repo, OrderSqlAlchemyRepository)


def test_get_current_user_returns_domain_user(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_session.add(
        UserModel(
            id="u-1",
            email="user@example.com",
            hashed_password="hashed",
            is_admin=True,
        )
    )
    db_session.commit()

    monkeypatch.setattr(deps, "decode_access_token", lambda _token: {"sub": "u-1"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    user = deps.get_current_user(credentials, db_session)

    assert user.id == "u-1"
    assert user.email == "user@example.com"
    assert user.is_admin is True


def test_get_current_user_raises_401_when_user_not_found(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps, "decode_access_token", lambda _token: {"sub": "missing"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with pytest.raises(HTTPException) as exc_info:
        deps.get_current_user(credentials, db_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"
