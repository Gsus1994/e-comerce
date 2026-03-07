from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.FastAPI.app.deps import (
    get_current_user,
    get_order_repo,
    get_product_repo,
    get_session,
)
from apps.FastAPI.app.schemas.order import CreateOrderRequest, OrderResponse
from packages.core.application.use_cases import create_order
from packages.core.domain.entities import CartItem, User
from packages.core.domain.exceptions import NotFound, StockInsufficient, ValidationError
from packages.core.infrastructure.repositories import (
    OrderSqlAlchemyRepository,
    ProductSqlAlchemyRepository,
)

router = APIRouter(prefix="/v1/orders", tags=["orders"])

CurrentUserDep = Annotated[User, Depends(get_current_user)]
ProductRepoDep = Annotated[ProductSqlAlchemyRepository, Depends(get_product_repo)]
OrderRepoDep = Annotated[OrderSqlAlchemyRepository, Depends(get_order_repo)]
SessionDep = Annotated[Session, Depends(get_session)]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_user_order(
    payload: CreateOrderRequest,
    current_user: CurrentUserDep,
    product_repo: ProductRepoDep,
    order_repo: OrderRepoDep,
    session: SessionDep,
) -> OrderResponse:
    cart_items = [CartItem(product_id=item.product_id, qty=item.qty) for item in payload.items]

    try:
        order = create_order(
            user_id=current_user.id,
            items=cart_items,
            product_repository=product_repo,
            order_repository=order_repo,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StockInsufficient as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    session.commit()
    return OrderResponse.from_entity(order)


@router.get("/me", response_model=list[OrderResponse])
def list_my_orders(current_user: CurrentUserDep, order_repo: OrderRepoDep) -> list[OrderResponse]:
    orders = order_repo.list_by_user(current_user.id)
    return [OrderResponse.from_entity(order) for order in orders]
