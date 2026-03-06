from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from apps.FastAPI.app.auth_utils import decode_access_token
from packages.core.domain.entities import User
from packages.core.infrastructure.db.models import UserModel
from packages.core.infrastructure.db.session import SessionLocal
from packages.core.infrastructure.repositories import (
    OrderSqlAlchemyRepository,
    ProductSqlAlchemyRepository,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials, Depends(security)]


def get_product_repo(session: SessionDep) -> ProductSqlAlchemyRepository:
    return ProductSqlAlchemyRepository(session)


def get_order_repo(session: SessionDep) -> OrderSqlAlchemyRepository:
    return OrderSqlAlchemyRepository(session)


def get_current_user(credentials: CredentialsDep, session: SessionDep) -> User:
    payload = decode_access_token(credentials.credentials)
    user_id = str(payload["sub"])

    user_model = session.scalar(select(UserModel).where(UserModel.id == user_id))
    if user_model is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return User(
        id=user_model.id,
        email=user_model.email,
        hashed_password=user_model.hashed_password,
        is_admin=user_model.is_admin,
    )
