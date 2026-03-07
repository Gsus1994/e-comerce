from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.FastAPI.app.deps import get_product_repo
from apps.FastAPI.app.schemas.product import (
    ProductListResponse,
    ProductPaginationMeta,
    ProductResponse,
)
from packages.core.application.use_cases import list_products as list_products_use_case
from packages.core.infrastructure.repositories import ProductSqlAlchemyRepository

router = APIRouter(prefix="/v1/products", tags=["products"])

ProductRepoDep = Annotated[ProductSqlAlchemyRepository, Depends(get_product_repo)]


@router.get("", response_model=ProductListResponse)
def list_products(
    product_repo: ProductRepoDep,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None),
) -> ProductListResponse:
    result = list_products_use_case(repository=product_repo, page=page, size=size, q=q)
    items = [ProductResponse.from_entity(product) for product in result["items"]]
    meta = ProductPaginationMeta.model_validate(result["meta"])
    return ProductListResponse(items=items, meta=meta)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, product_repo: ProductRepoDep) -> ProductResponse:
    product = product_repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    return ProductResponse.from_entity(product)
