from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from apps.FastAPI.app.deps import get_product_repo
from apps.FastAPI.app.schemas.order import (
    CartValidateRequest,
    CartValidateResponse,
    CartValidationItem,
)
from packages.core.application.use_cases import add_to_cart
from packages.core.domain.entities import Cart
from packages.core.domain.exceptions import ValidationError
from packages.core.infrastructure.repositories import ProductSqlAlchemyRepository

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/v1/cart", tags=["cart"])

ProductRepoDep = Annotated[ProductSqlAlchemyRepository, Depends(get_product_repo)]


@router.post("/validate", response_model=CartValidateResponse)
def validate_cart(
    payload: CartValidateRequest, product_repo: ProductRepoDep
) -> CartValidateResponse:
    cart = Cart()
    try:
        for item in payload.items:
            add_to_cart(cart=cart, product_id=item.product_id, qty=item.qty)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    response_items: list[CartValidationItem] = []
    total = Decimal("0")

    for cart_item in cart.items:
        product = product_repo.get_by_id(cart_item.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{cart_item.product_id}' not found",
            )
        if product.stock < cart_item.qty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for product '{product.id}'",
            )

        subtotal = product.price * cart_item.qty
        total += subtotal
        response_items.append(
            CartValidationItem(
                product_id=product.id,
                qty=cart_item.qty,
                unit_price=float(product.price),
                subtotal=float(subtotal),
            ),
        )

    return CartValidateResponse(items=response_items, total=float(total))
