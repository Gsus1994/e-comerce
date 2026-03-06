from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import pbkdf2_hmac
from secrets import compare_digest, token_hex
from typing import Any, cast

import jwt
from apps.FastAPI.app.settings import get_settings

from fastapi import HTTPException, status

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
PBKDF2_ITERATIONS = 390000


def hash_password(password: str) -> str:
    salt = token_hex(16)
    digest = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        _, rounds, salt, expected_digest = hashed_password.split("$", maxsplit=3)
        digest = pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(rounds),
        ).hex()
    except (ValueError, TypeError):
        return False
    return compare_digest(digest, expected_digest)


def _build_python_jwt_hmac_key(secret: str) -> Any:
    jwk_module = getattr(jwt, "jwk", None)
    octet_jwk = getattr(jwk_module, "OctetJWK", None) if jwk_module else None
    if octet_jwk is None:  # pragma: no cover - defensive branch
        raise RuntimeError("Unsupported jwt package installed: missing jwk.OctetJWK")
    return octet_jwk(secret.encode("utf-8"))


def _encode_jwt(payload: dict[str, Any], secret: str) -> str:
    encode_fn = getattr(jwt, "encode", None)
    if callable(encode_fn):
        return cast(str, encode_fn(payload, secret, algorithm=ALGORITHM))

    jwt_class = getattr(jwt, "JWT", None)
    if jwt_class is None:  # pragma: no cover - defensive branch
        raise RuntimeError("No compatible JWT encoder found.")
    key = _build_python_jwt_hmac_key(secret)
    return cast(str, jwt_class().encode(payload, key=key, alg=ALGORITHM))


def _decode_jwt(token: str, secret: str) -> dict[str, Any]:
    decode_fn = getattr(jwt, "decode", None)
    if callable(decode_fn):
        return cast(dict[str, Any], decode_fn(token, secret, algorithms=[ALGORITHM]))

    jwt_class = getattr(jwt, "JWT", None)
    if jwt_class is None:  # pragma: no cover - defensive branch
        raise RuntimeError("No compatible JWT decoder found.")
    key = _build_python_jwt_hmac_key(secret)
    return cast(dict[str, Any], jwt_class().decode(token, key=key, algorithms={ALGORITHM}))


def _jwt_error_types() -> tuple[type[Exception], ...]:
    error_types: list[type[Exception]] = []

    pyjwt_error = getattr(jwt, "PyJWTError", None)
    if isinstance(pyjwt_error, type) and issubclass(pyjwt_error, Exception):
        error_types.append(pyjwt_error)

    exceptions_module = getattr(jwt, "exceptions", None)
    if exceptions_module is not None:
        for name in ("JWTException", "JWTDecodeError", "JWSDecodeError"):
            error_type = getattr(exceptions_module, name, None)
            if isinstance(error_type, type) and issubclass(error_type, Exception):
                error_types.append(error_type)

    return tuple(dict.fromkeys(error_types)) or (ValueError,)


def create_access_token(
    *,
    subject: str,
    email: str,
    is_admin: bool,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    expire_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "is_admin": is_admin,
        "exp": int(expire_at.timestamp()),
    }
    return _encode_jwt(payload, settings.jwt_secret)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    jwt_error_types = _jwt_error_types()
    try:
        payload = _decode_jwt(token, settings.jwt_secret)
    except jwt_error_types as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return payload
