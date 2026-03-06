from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import pbkdf2_hmac
from secrets import compare_digest, token_hex
from typing import Any

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
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:  # pragma: no cover - defensive branch
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
