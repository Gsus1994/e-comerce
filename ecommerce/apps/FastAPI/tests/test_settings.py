from __future__ import annotations

from collections.abc import Generator

import pytest

from apps.FastAPI.app.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_parse_cors_origins_from_string() -> None:
    settings = Settings.model_validate({"CORS_ORIGINS": "https://a.example, https://b.example"})

    assert settings.cors_origins == ["https://a.example", "https://b.example"]


def test_settings_accept_cors_origins_list() -> None:
    settings = Settings.model_validate({"CORS_ORIGINS": ["https://a.example", "https://b.example"]})

    assert settings.cors_origins == ["https://a.example", "https://b.example"]


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "first-secret")
    first = get_settings()

    monkeypatch.setenv("JWT_SECRET", "second-secret")
    second = get_settings()

    assert first is second
    assert second.jwt_secret == "first-secret"


def test_get_settings_reloads_after_cache_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "first-secret")
    _ = get_settings()

    monkeypatch.setenv("JWT_SECRET", "second-secret")
    get_settings.cache_clear()
    refreshed = get_settings()

    assert refreshed.jwt_secret == "second-secret"
