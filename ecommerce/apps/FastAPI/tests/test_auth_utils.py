from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from apps.FastAPI.app import auth_utils


@dataclass(frozen=True, slots=True)
class _TestSettings:
    jwt_secret: str


def test_hash_password_and_verify_password_roundtrip() -> None:
    hashed = auth_utils.hash_password("strongpass1")

    assert hashed.startswith(f"pbkdf2_sha256${auth_utils.PBKDF2_ITERATIONS}$")
    assert auth_utils.verify_password("strongpass1", hashed) is True
    assert auth_utils.verify_password("wrongpass", hashed) is False


def test_verify_password_returns_false_for_invalid_hash_format() -> None:
    assert auth_utils.verify_password("strongpass1", "not-a-valid-hash") is False


def test_create_and_decode_access_token_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_utils, "get_settings", lambda: _TestSettings(jwt_secret="secret"))

    token = auth_utils.create_access_token(subject="u-1", email="user@example.com", is_admin=False)
    payload = auth_utils.decode_access_token(token)

    assert payload["sub"] == "u-1"
    assert payload["email"] == "user@example.com"
    assert payload["is_admin"] is False
    assert "exp" in payload


def test_decode_access_token_rejects_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_utils, "get_settings", lambda: _TestSettings(jwt_secret="secret"))

    with pytest.raises(HTTPException) as exc_info:
        auth_utils.decode_access_token("invalid-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token"


def test_decode_access_token_requires_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_utils, "get_settings", lambda: _TestSettings(jwt_secret="secret"))
    token = auth_utils._encode_jwt({"email": "user@example.com", "is_admin": False}, "secret")

    with pytest.raises(HTTPException) as exc_info:
        auth_utils.decode_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token payload"


def test_encode_jwt_uses_callable_encode(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_encode(payload: dict[str, Any], secret: str, *, algorithm: str) -> str:
        captured["payload"] = payload
        captured["secret"] = secret
        captured["algorithm"] = algorithm
        return "encoded-token"

    monkeypatch.setattr(auth_utils, "jwt", SimpleNamespace(encode=fake_encode))

    token = auth_utils._encode_jwt({"sub": "u-1"}, "secret")

    assert token == "encoded-token"
    assert captured["payload"] == {"sub": "u-1"}
    assert captured["secret"] == "secret"
    assert captured["algorithm"] == auth_utils.ALGORITHM


def test_decode_jwt_uses_callable_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_decode(token: str, secret: str, *, algorithms: list[str]) -> dict[str, Any]:
        captured["token"] = token
        captured["secret"] = secret
        captured["algorithms"] = algorithms
        return {"sub": "u-1"}

    monkeypatch.setattr(auth_utils, "jwt", SimpleNamespace(decode=fake_decode))

    payload = auth_utils._decode_jwt("token", "secret")

    assert payload == {"sub": "u-1"}
    assert captured["token"] == "token"
    assert captured["secret"] == "secret"
    assert captured["algorithms"] == [auth_utils.ALGORITHM]


def test_encode_jwt_falls_back_to_jwt_class(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeOctetJWK:
        def __init__(self, key_bytes: bytes) -> None:
            captured["key_bytes"] = key_bytes

    class FakeJWT:
        def encode(self, payload: dict[str, Any], *, key: Any, alg: str) -> str:
            captured["payload"] = payload
            captured["key"] = key
            captured["alg"] = alg
            return "fallback-encoded-token"

    fake_jwt = SimpleNamespace(
        encode=None,
        JWT=lambda: FakeJWT(),
        jwk=SimpleNamespace(OctetJWK=FakeOctetJWK),
    )
    monkeypatch.setattr(auth_utils, "jwt", fake_jwt)

    token = auth_utils._encode_jwt({"sub": "u-1"}, "secret")

    assert token == "fallback-encoded-token"
    assert captured["payload"] == {"sub": "u-1"}
    assert isinstance(captured["key"], FakeOctetJWK)
    assert captured["key_bytes"] == b"secret"
    assert captured["alg"] == auth_utils.ALGORITHM


def test_decode_jwt_falls_back_to_jwt_class(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeOctetJWK:
        def __init__(self, key_bytes: bytes) -> None:
            captured["key_bytes"] = key_bytes

    class FakeJWT:
        def decode(self, token: str, *, key: Any, algorithms: set[str]) -> dict[str, Any]:
            captured["token"] = token
            captured["key"] = key
            captured["algorithms"] = algorithms
            return {"sub": "u-1"}

    fake_jwt = SimpleNamespace(
        decode=None,
        JWT=lambda: FakeJWT(),
        jwk=SimpleNamespace(OctetJWK=FakeOctetJWK),
    )
    monkeypatch.setattr(auth_utils, "jwt", fake_jwt)

    payload = auth_utils._decode_jwt("token", "secret")

    assert payload == {"sub": "u-1"}
    assert captured["token"] == "token"
    assert isinstance(captured["key"], FakeOctetJWK)
    assert captured["key_bytes"] == b"secret"
    assert captured["algorithms"] == {auth_utils.ALGORITHM}


def test_jwt_error_types_includes_root_level_pyjwt_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RootPyJwtError(Exception):
        pass

    fake_jwt = SimpleNamespace(
        PyJWTError=RootPyJwtError,
        exceptions=SimpleNamespace(),
    )
    monkeypatch.setattr(auth_utils, "jwt", fake_jwt)

    error_types = auth_utils._jwt_error_types()

    assert RootPyJwtError in error_types


def test_jwt_error_types_includes_module_level_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class ModuleJwtError(Exception):
        pass

    class ModuleDecodeError(Exception):
        pass

    fake_jwt = SimpleNamespace(
        PyJWTError=None,
        exceptions=SimpleNamespace(
            JWTException=ModuleJwtError,
            JWTDecodeError=ModuleDecodeError,
            JWSDecodeError="not-an-exception-type",
        ),
    )
    monkeypatch.setattr(auth_utils, "jwt", fake_jwt)

    error_types = auth_utils._jwt_error_types()

    assert ModuleJwtError in error_types
    assert ModuleDecodeError in error_types
