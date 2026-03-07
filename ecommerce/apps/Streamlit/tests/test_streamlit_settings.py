from __future__ import annotations

import pytest

from apps.Streamlit.settings import get_settings


def test_get_settings_uses_default_base_url_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("API_BASE_URL", raising=False)

    settings = get_settings()

    assert settings.api_base_url == "http://localhost:8000"


def test_get_settings_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "http://api.local:9000/")

    settings = get_settings()

    assert settings.api_base_url == "http://api.local:9000"
