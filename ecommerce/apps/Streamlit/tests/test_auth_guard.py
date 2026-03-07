from __future__ import annotations

import pytest

from apps.Streamlit import auth_guard


class StopCalled(RuntimeError):
    pass


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.calls: list[tuple[object, ...]] = []

    def switch_page(self, target: str) -> None:
        self.calls.append(("switch_page", target))

    def warning(self, message: str) -> None:
        self.calls.append(("warning", message))

    def page_link(self, page: str, *, label: str) -> None:
        self.calls.append(("page_link", page, label))

    def stop(self) -> None:
        self.calls.append(("stop",))
        raise StopCalled("st.stop called")


class MinimalFakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.calls: list[tuple[object, ...]] = []

    def warning(self, message: str) -> None:
        self.calls.append(("warning", message))

    def stop(self) -> None:
        self.calls.append(("stop",))
        raise StopCalled("st.stop called")


def test_init_session_state_sets_defaults_without_overwriting_existing_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["cart"] = {"p-1": {"qty": 1}}
    fake_st.session_state["auth_token"] = "token"

    monkeypatch.setattr(auth_guard, "st", fake_st)
    auth_guard.init_session_state()

    assert fake_st.session_state["cart"] == {"p-1": {"qty": 1}}
    assert fake_st.session_state["auth_token"] == "token"
    assert fake_st.session_state["auth_user"] is None
    assert fake_st.session_state["cart_validation"] is None
    assert fake_st.session_state["last_order"] is None


def test_clear_auth_session_resets_token_and_user(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["auth_token"] = "token"
    fake_st.session_state["auth_user"] = {"id": "u-1"}

    monkeypatch.setattr(auth_guard, "st", fake_st)
    auth_guard.clear_auth_session()

    assert fake_st.session_state["auth_token"] == ""
    assert fake_st.session_state["auth_user"] is None


def test_require_auth_returns_token_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["auth_token"] = "valid-token"

    monkeypatch.setattr(auth_guard, "st", fake_st)

    token = auth_guard.require_auth()

    assert token == "valid-token"
    assert fake_st.calls == []


def test_require_auth_redirects_and_stops_when_missing_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(auth_guard, "st", fake_st)

    with pytest.raises(StopCalled):
        auth_guard.require_auth("Debes iniciar sesion")

    assert ("switch_page", "pages/0_auth.py") in fake_st.calls
    assert ("warning", "Debes iniciar sesion") in fake_st.calls
    assert ("page_link", "pages/0_auth.py", "Ir a Auth") in fake_st.calls
    assert ("stop",) in fake_st.calls


def test_require_auth_without_navigation_helpers_still_warns_and_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = MinimalFakeStreamlit()
    monkeypatch.setattr(auth_guard, "st", fake_st)

    with pytest.raises(StopCalled):
        auth_guard.require_auth("Login requerido")

    assert fake_st.calls == [("warning", "Login requerido"), ("stop",)]
