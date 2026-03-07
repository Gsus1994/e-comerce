from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from apps.Streamlit.client.api_client import ApiClient


@pytest.mark.parametrize(
    ("q", "expected_params"),
    [
        (None, {"page": 2, "size": 10}),
        ("", {"page": 2, "size": 10}),
        (" ", {"page": 2, "size": 10, "q": " "}),
        ("phone", {"page": 2, "size": 10, "q": "phone"}),
        ("PHONE", {"page": 2, "size": 10, "q": "PHONE"}),
    ],
)
def test_get_products_query_param_contract(
    monkeypatch: pytest.MonkeyPatch,
    q: str | None,
    expected_params: dict[str, Any],
) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        self: ApiClient,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        captured["method"] = method
        captured["path"] = path
        captured["token"] = token
        captured["params"] = params
        captured["json_body"] = json_body
        return {"items": [], "meta": {}}

    monkeypatch.setattr(ApiClient, "_request", fake_request)
    client = ApiClient("http://api.local")

    result = client.get_products(page=2, size=10, q=q)

    assert result == {"items": [], "meta": {}}
    assert captured == {
        "method": "GET",
        "path": "/v1/products",
        "token": None,
        "params": expected_params,
        "json_body": None,
    }


@pytest.mark.parametrize(
    ("runner", "expected"),
    [
        (
            lambda c: c.get_product("p-1"),
            {
                "method": "GET",
                "path": "/v1/products/p-1",
                "token": None,
                "params": None,
                "json_body": None,
            },
        ),
        (
            lambda c: c.register(email="user@example.com", password="strongpass1"),
            {
                "method": "POST",
                "path": "/v1/auth/register",
                "token": None,
                "params": None,
                "json_body": {"email": "user@example.com", "password": "strongpass1"},
            },
        ),
        (
            lambda c: c.login(email="user@example.com", password="strongpass1"),
            {
                "method": "POST",
                "path": "/v1/auth/login",
                "token": None,
                "params": None,
                "json_body": {"email": "user@example.com", "password": "strongpass1"},
            },
        ),
        (
            lambda c: c.recover_password(email="user@example.com", new_password="newstrongpass1"),
            {
                "method": "POST",
                "path": "/v1/auth/recover-password",
                "token": None,
                "params": None,
                "json_body": {
                    "email": "user@example.com",
                    "new_password": "newstrongpass1",
                },
            },
        ),
        (
            lambda c: c.validate_cart(items=[{"product_id": "p-1", "qty": 2}]),
            {
                "method": "POST",
                "path": "/v1/cart/validate",
                "token": None,
                "params": None,
                "json_body": {"items": [{"product_id": "p-1", "qty": 2}]},
            },
        ),
        (
            lambda c: c.create_order(items=[{"product_id": "p-1", "qty": 1}], token="jwt"),
            {
                "method": "POST",
                "path": "/v1/orders",
                "token": "jwt",
                "params": None,
                "json_body": {"items": [{"product_id": "p-1", "qty": 1}]},
            },
        ),
        (
            lambda c: c.list_my_orders(token="jwt"),
            {
                "method": "GET",
                "path": "/v1/orders/me",
                "token": "jwt",
                "params": None,
                "json_body": None,
            },
        ),
    ],
)
def test_api_client_methods_forward_http_contract(
    monkeypatch: pytest.MonkeyPatch,
    runner: Callable[[ApiClient], object],
    expected: dict[str, Any],
) -> None:
    captured: dict[str, Any] = {}

    def fake_request(
        self: ApiClient,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> object:
        captured.update(
            {
                "method": method,
                "path": path,
                "token": token,
                "params": params,
                "json_body": json_body,
            }
        )
        if path == "/v1/orders/me":
            return []
        return {"ok": True}

    monkeypatch.setattr(ApiClient, "_request", fake_request)
    client = ApiClient("http://api.local")

    runner(client)

    assert captured == expected
