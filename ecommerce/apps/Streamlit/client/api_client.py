from __future__ import annotations

from typing import Any, TypedDict

import httpx


class CartItemPayload(TypedDict):
    product_id: str
    qty: int


class ApiClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
                response = client.request(
                    method,
                    path,
                    headers=headers,
                    params=params,
                    json=json_body,
                )
        except httpx.RequestError as exc:
            raise ApiClientError(f"Network error: {exc}") from exc

        if response.is_success:
            if not response.content:
                return {}
            return response.json()

        detail = response.text
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = str(payload.get("detail", payload))
            else:
                detail = str(payload)
        except ValueError:
            detail = response.text

        raise ApiClientError(
            message=f"API error ({response.status_code}): {detail}",
            status_code=response.status_code,
        )

    def get_products(
        self, *, page: int = 1, size: int = 20, q: str | None = None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "size": size}
        if q:
            params["q"] = q
        result = self._request("GET", "/v1/products", params=params)
        if not isinstance(result, dict):
            raise ApiClientError("Unexpected response format for products list")
        return result

    def get_product(self, product_id: str) -> dict[str, Any]:
        result = self._request("GET", f"/v1/products/{product_id}")
        if not isinstance(result, dict):
            raise ApiClientError("Unexpected response format for product detail")
        return result

    def register(self, *, email: str, password: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/v1/auth/register",
            json_body={"email": email, "password": password},
        )
        if not isinstance(result, dict):
            raise ApiClientError("Unexpected response format for register")
        return result

    def login(self, *, email: str, password: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/v1/auth/login",
            json_body={"email": email, "password": password},
        )
        if not isinstance(result, dict):
            raise ApiClientError("Unexpected response format for login")
        return result

    def validate_cart(self, *, items: list[CartItemPayload]) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/v1/cart/validate",
            json_body={"items": items},
        )
        if not isinstance(result, dict):
            raise ApiClientError("Unexpected response format for cart validation")
        return result

    def create_order(self, *, items: list[CartItemPayload], token: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/v1/orders",
            token=token,
            json_body={"items": items},
        )
        if not isinstance(result, dict):
            raise ApiClientError("Unexpected response format for create order")
        return result

    def list_my_orders(self, *, token: str) -> list[dict[str, Any]]:
        result = self._request("GET", "/v1/orders/me", token=token)
        if not isinstance(result, list):
            raise ApiClientError("Unexpected response format for orders list")
        return [item for item in result if isinstance(item, dict)]
