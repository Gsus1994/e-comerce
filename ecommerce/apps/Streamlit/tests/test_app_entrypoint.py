from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from apps.Streamlit import auth_guard, settings


class FakeColumn:
    def __init__(self, name: str, calls: list[tuple[Any, ...]]) -> None:
        self._name = name
        self._calls = calls

    def metric(self, label: str, value: object) -> None:
        self._calls.append(("metric", self._name, label, value))


def _build_fake_streamlit(
    *,
    with_page_link: bool,
    session_state: dict[str, object],
) -> tuple[ModuleType, list[tuple[Any, ...]]]:
    calls: list[tuple[Any, ...]] = []
    fake_module = ModuleType("streamlit")
    fake_module.session_state = session_state  # type: ignore[attr-defined]

    def set_page_config(*, page_title: str, layout: str) -> None:
        calls.append(("set_page_config", page_title, layout))

    def title(text: str) -> None:
        calls.append(("title", text))

    def caption(text: str) -> None:
        calls.append(("caption", text))

    def columns(count: int) -> tuple[FakeColumn, FakeColumn]:
        calls.append(("columns", count))
        return FakeColumn("col1", calls), FakeColumn("col2", calls)

    def markdown(text: str) -> None:
        calls.append(("markdown", text))

    def write(text: str) -> None:
        calls.append(("write", text))

    fake_module.set_page_config = set_page_config  # type: ignore[attr-defined]
    fake_module.title = title  # type: ignore[attr-defined]
    fake_module.caption = caption  # type: ignore[attr-defined]
    fake_module.columns = columns  # type: ignore[attr-defined]
    fake_module.markdown = markdown  # type: ignore[attr-defined]
    fake_module.write = write  # type: ignore[attr-defined]

    if with_page_link:

        def page_link(page: str, *, label: str) -> None:
            calls.append(("page_link", page, label))

        fake_module.page_link = page_link  # type: ignore[attr-defined]

    return fake_module, calls


def _run_streamlit_app_module(
    monkeypatch: pytest.MonkeyPatch,
    *,
    with_page_link: bool,
    initial_session_state: dict[str, object],
) -> list[tuple[Any, ...]]:
    fake_st, calls = _build_fake_streamlit(
        with_page_link=with_page_link,
        session_state=initial_session_state,
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)

    def fake_init_session_state() -> None:
        fake_st.session_state.setdefault("cart", {})
        fake_st.session_state.setdefault("auth_token", "")
        fake_st.session_state.setdefault("auth_user", None)
        fake_st.session_state.setdefault("cart_validation", None)
        fake_st.session_state.setdefault("last_order", None)

    monkeypatch.setattr(auth_guard, "init_session_state", fake_init_session_state)
    monkeypatch.setattr(
        settings,
        "get_settings",
        lambda: SimpleNamespace(api_base_url="http://api.local"),
    )

    sys.modules.pop("apps.Streamlit.app", None)
    importlib.import_module("apps.Streamlit.app")
    return calls


def test_streamlit_app_renders_navigation_with_page_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _run_streamlit_app_module(
        monkeypatch,
        with_page_link=True,
        initial_session_state={
            "cart": {"p-1": {"qty": 2}, "p-2": {"qty": 1}},
            "auth_token": "jwt-token",
            "auth_user": {"email": "user@example.com"},
        },
    )

    assert ("set_page_config", "Ecommerce MVP", "wide") in calls
    assert ("title", "Ecommerce MVP") in calls
    assert ("caption", "API base URL: http://api.local") in calls
    assert ("metric", "col1", "Items en carrito", 2) in calls
    assert ("metric", "col2", "Sesion", "Activa") in calls
    assert ("caption", "Usuario actual: user@example.com") in calls
    assert ("markdown", "### Navegacion") in calls

    page_links = [call for call in calls if call[0] == "page_link"]
    assert len(page_links) == 5
    assert ("page_link", "pages/0_auth.py", "Auth (Login/Registro)") in page_links
    assert ("page_link", "pages/1_catalogo.py", "Catalogo") in page_links
    assert ("page_link", "pages/2_carrito.py", "Carrito") in page_links
    assert ("page_link", "pages/3_checkout.py", "Checkout") in page_links
    assert ("page_link", "pages/4_mis_pedidos.py", "Mis pedidos") in page_links
    assert all(call[0] != "write" for call in calls)


def test_streamlit_app_uses_fallback_text_without_page_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _run_streamlit_app_module(
        monkeypatch,
        with_page_link=False,
        initial_session_state={"cart": {}, "auth_token": "", "auth_user": None},
    )

    assert ("metric", "col1", "Items en carrito", 0) in calls
    assert ("metric", "col2", "Sesion", "No autenticada") in calls
    assert (
        "write",
        "Usa el menu lateral de Streamlit para navegar entre paginas.",
    ) in calls
    assert all(call[0] != "page_link" for call in calls)
