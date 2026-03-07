from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from apps.Streamlit.client import api_client
from apps.Streamlit.client.api_client import ApiClient, ApiClientError


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        content: bytes,
        payload: Any = None,
        text: str = "",
        json_raises: bool = False,
    ) -> None:
        self.status_code = status_code
        self.content = content
        self._payload = payload
        self.text = text
        self._json_raises = json_raises

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if self._json_raises:
            raise ValueError("invalid json")
        return self._payload


def _patch_http_client(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[
        [str, str, dict[str, str], dict[str, Any] | None, dict[str, Any] | None], FakeResponse
    ],
    capture: dict[str, Any],
) -> None:
    class FakeHttpxClient:
        def __init__(self, *, base_url: str, timeout: float) -> None:
            capture["base_url"] = base_url
            capture["timeout"] = timeout

        def __enter__(self) -> FakeHttpxClient:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        def request(
            self,
            method: str,
            path: str,
            *,
            headers: dict[str, str],
            params: dict[str, Any] | None,
            json: dict[str, Any] | None,
        ) -> FakeResponse:
            capture["request"] = {
                "method": method,
                "path": path,
                "headers": headers,
                "params": params,
                "json": json,
            }
            return handler(method, path, headers, params, json)

    monkeypatch.setattr(api_client.httpx, "Client", FakeHttpxClient)


def test_request_returns_json_and_includes_auth_header(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, Any] = {}

    def handler(
        method: str,
        path: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        json_body: dict[str, Any] | None,
    ) -> FakeResponse:
        assert method == "GET"
        assert path == "/v1/products"
        assert params == {"page": 1}
        assert json_body is None
        assert headers["Authorization"] == "Bearer token"
        return FakeResponse(status_code=200, content=b"{}", payload={"ok": True})

    _patch_http_client(monkeypatch, handler, capture)

    client = ApiClient("http://api.local/")
    payload = client._request("GET", "/v1/products", token="token", params={"page": 1})

    assert payload == {"ok": True}
    assert capture["base_url"] == "http://api.local"
    assert capture["timeout"] == 10.0


def test_request_returns_empty_dict_for_empty_body(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, Any] = {}

    def handler(
        _method: str,
        _path: str,
        _headers: dict[str, str],
        _params: dict[str, Any] | None,
        _json_body: dict[str, Any] | None,
    ) -> FakeResponse:
        return FakeResponse(status_code=204, content=b"", payload=None)

    _patch_http_client(monkeypatch, handler, capture)

    client = ApiClient("http://api.local")
    payload = client._request("GET", "/ping")

    assert payload == {}


def test_request_wraps_network_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, Any] = {}

    def handler(
        _method: str,
        _path: str,
        _headers: dict[str, str],
        _params: dict[str, Any] | None,
        _json_body: dict[str, Any] | None,
    ) -> FakeResponse:
        raise api_client.httpx.RequestError("network down")

    _patch_http_client(monkeypatch, handler, capture)

    client = ApiClient("http://api.local")

    with pytest.raises(ApiClientError, match="Network error"):
        client._request("GET", "/ping")


def test_request_uses_detail_field_from_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, Any] = {}

    def handler(
        _method: str,
        _path: str,
        _headers: dict[str, str],
        _params: dict[str, Any] | None,
        _json_body: dict[str, Any] | None,
    ) -> FakeResponse:
        return FakeResponse(
            status_code=400,
            content=b'{"detail":"bad request"}',
            payload={"detail": "bad request"},
            text='{"detail":"bad request"}',
        )

    _patch_http_client(monkeypatch, handler, capture)

    client = ApiClient("http://api.local")

    with pytest.raises(ApiClientError) as exc_info:
        client._request("POST", "/v1/orders")

    assert exc_info.value.status_code == 400
    assert str(exc_info.value) == "API error (400): bad request"


def test_request_falls_back_to_text_when_error_body_is_not_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture: dict[str, Any] = {}

    def handler(
        _method: str,
        _path: str,
        _headers: dict[str, str],
        _params: dict[str, Any] | None,
        _json_body: dict[str, Any] | None,
    ) -> FakeResponse:
        return FakeResponse(
            status_code=500,
            content=b"internal error",
            payload=None,
            text="internal error",
            json_raises=True,
        )

    _patch_http_client(monkeypatch, handler, capture)

    client = ApiClient("http://api.local")

    with pytest.raises(ApiClientError) as exc_info:
        client._request("GET", "/v1/products")

    assert exc_info.value.status_code == 500
    assert str(exc_info.value) == "API error (500): internal error"


def test_request_uses_stringified_non_dict_json_payload_for_error_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture: dict[str, Any] = {}

    def handler(
        _method: str,
        _path: str,
        _headers: dict[str, str],
        _params: dict[str, Any] | None,
        _json_body: dict[str, Any] | None,
    ) -> FakeResponse:
        return FakeResponse(
            status_code=422,
            content=b"[]",
            payload=["invalid", "payload"],
            text="[]",
        )

    _patch_http_client(monkeypatch, handler, capture)

    client = ApiClient("http://api.local")

    with pytest.raises(ApiClientError) as exc_info:
        client._request("POST", "/v1/auth/login")

    assert exc_info.value.status_code == 422
    assert str(exc_info.value) == "API error (422): ['invalid', 'payload']"


def test_get_products_raises_when_response_is_not_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ApiClient,
        "_request",
        lambda self, method, path, *, token=None, params=None, json_body=None: ["invalid"],
    )
    client = ApiClient("http://api.local")

    with pytest.raises(ApiClientError, match="Unexpected response format for products list"):
        client.get_products()


def test_get_products_passes_query_param(monkeypatch: pytest.MonkeyPatch) -> None:
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

    payload = client.get_products(page=2, size=30, q="phone")

    assert payload == {"items": [], "meta": {}}
    assert captured["method"] == "GET"
    assert captured["path"] == "/v1/products"
    assert captured["token"] is None
    assert captured["params"] == {"page": 2, "size": 30, "q": "phone"}
    assert captured["json_body"] is None


def test_list_my_orders_filters_out_non_dict_items(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ApiClient,
        "_request",
        lambda self, method, path, *, token=None, params=None, json_body=None: [
            {"id": "o-1"},
            "invalid",
            123,
            {"id": "o-2"},
        ],
    )
    client = ApiClient("http://api.local")

    orders = client.list_my_orders(token="token")

    assert orders == [{"id": "o-1"}, {"id": "o-2"}]


def test_create_order_passes_token_and_payload(monkeypatch: pytest.MonkeyPatch) -> None:
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
        return {"id": "o-1"}

    monkeypatch.setattr(ApiClient, "_request", fake_request)
    client = ApiClient("http://api.local")

    response = client.create_order(
        items=[{"product_id": "p-1", "qty": 2}],
        token="jwt-token",
    )

    assert response == {"id": "o-1"}
    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/orders"
    assert captured["token"] == "jwt-token"
    assert captured["params"] is None
    assert captured["json_body"] == {"items": [{"product_id": "p-1", "qty": 2}]}


@pytest.mark.parametrize(
    ("caller", "expected_message"),
    [
        (
            lambda client: client.get_product("p-1"),
            "Unexpected response format for product detail",
        ),
        (
            lambda client: client.register(email="user@example.com", password="strongpass1"),
            "Unexpected response format for register",
        ),
        (
            lambda client: client.login(email="user@example.com", password="strongpass1"),
            "Unexpected response format for login",
        ),
        (
            lambda client: client.recover_password(
                email="user@example.com",
                new_password="newstrongpass1",
            ),
            "Unexpected response format for recover password",
        ),
        (
            lambda client: client.validate_cart(items=[{"product_id": "p-1", "qty": 1}]),
            "Unexpected response format for cart validation",
        ),
        (
            lambda client: client.create_order(
                items=[{"product_id": "p-1", "qty": 1}],
                token="jwt-token",
            ),
            "Unexpected response format for create order",
        ),
        (
            lambda client: client.list_my_orders(token="jwt-token"),
            "Unexpected response format for orders list",
        ),
    ],
)
def test_methods_raise_when_response_shape_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
    caller: Callable[[ApiClient], object],
    expected_message: str,
) -> None:
    monkeypatch.setattr(
        ApiClient,
        "_request",
        lambda self, method, path, *, token=None, params=None, json_body=None: "invalid",
    )
    client = ApiClient("http://api.local")

    with pytest.raises(ApiClientError, match=expected_message):
        caller(client)


def test_auth_methods_and_get_product_forward_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_calls: list[dict[str, Any]] = []

    def fake_request(
        self: ApiClient,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        captured_calls.append(
            {
                "method": method,
                "path": path,
                "token": token,
                "params": params,
                "json_body": json_body,
            }
        )
        return {"ok": True}

    monkeypatch.setattr(ApiClient, "_request", fake_request)
    client = ApiClient("http://api.local")

    assert client.get_product("p-10") == {"ok": True}
    assert client.register(email="user@example.com", password="strongpass1") == {"ok": True}
    assert client.login(email="user@example.com", password="strongpass1") == {"ok": True}
    assert client.recover_password(
        email="user@example.com",
        new_password="newstrongpass1",
    ) == {"ok": True}
    assert client.validate_cart(items=[{"product_id": "p-1", "qty": 2}]) == {"ok": True}

    assert captured_calls == [
        {
            "method": "GET",
            "path": "/v1/products/p-10",
            "token": None,
            "params": None,
            "json_body": None,
        },
        {
            "method": "POST",
            "path": "/v1/auth/register",
            "token": None,
            "params": None,
            "json_body": {"email": "user@example.com", "password": "strongpass1"},
        },
        {
            "method": "POST",
            "path": "/v1/auth/login",
            "token": None,
            "params": None,
            "json_body": {"email": "user@example.com", "password": "strongpass1"},
        },
        {
            "method": "POST",
            "path": "/v1/auth/recover-password",
            "token": None,
            "params": None,
            "json_body": {"email": "user@example.com", "new_password": "newstrongpass1"},
        },
        {
            "method": "POST",
            "path": "/v1/cart/validate",
            "token": None,
            "params": None,
            "json_body": {"items": [{"product_id": "p-1", "qty": 2}]},
        },
    ]
