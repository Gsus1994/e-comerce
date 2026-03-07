from __future__ import annotations

from typing import Any

import pytest

from packages.core.infrastructure.db import session as session_module


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closes += 1


def test_resolve_database_url_uses_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")

    assert session_module._resolve_database_url() == "postgresql://example"


def test_resolve_database_url_uses_default_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert session_module._resolve_database_url() == session_module.DEFAULT_DATABASE_URL


def test_create_engine_from_url_passes_sqlite_connect_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    fake_engine = object()

    def fake_create_engine(url: str, connect_args: dict[str, bool]) -> object:
        captured["url"] = url
        captured["connect_args"] = connect_args
        return fake_engine

    monkeypatch.setattr(session_module, "create_engine", fake_create_engine)

    created = session_module.create_engine_from_url("sqlite+pysqlite:///:memory:")

    assert created is fake_engine
    assert captured["url"] == "sqlite+pysqlite:///:memory:"
    assert captured["connect_args"] == {"check_same_thread": False}


def test_create_engine_from_url_uses_empty_connect_args_for_non_sqlite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_create_engine(url: str, connect_args: dict[str, bool]) -> object:
        captured["url"] = url
        captured["connect_args"] = connect_args
        return object()

    monkeypatch.setattr(session_module, "create_engine", fake_create_engine)

    session_module.create_engine_from_url("postgresql+psycopg://localhost/db")

    assert captured["connect_args"] == {}


def test_session_scope_commits_and_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(session_module, "SessionLocal", lambda: fake_session)

    with session_module.session_scope() as current_session:
        assert current_session is fake_session

    assert fake_session.commits == 1
    assert fake_session.rollbacks == 0
    assert fake_session.closes == 1


def test_session_scope_rolls_back_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(session_module, "SessionLocal", lambda: fake_session)

    with pytest.raises(RuntimeError, match="boom"):
        with session_module.session_scope():
            raise RuntimeError("boom")

    assert fake_session.commits == 0
    assert fake_session.rollbacks == 1
    assert fake_session.closes == 1
