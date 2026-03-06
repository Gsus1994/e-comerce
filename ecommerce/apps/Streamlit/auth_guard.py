from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    st.session_state.setdefault("cart", {})
    st.session_state.setdefault("auth_token", "")
    st.session_state.setdefault("auth_user", None)
    st.session_state.setdefault("cart_validation", None)
    st.session_state.setdefault("last_order", None)


def get_auth_token() -> str:
    return str(st.session_state.get("auth_token", ""))


def clear_auth_session() -> None:
    st.session_state["auth_token"] = ""
    st.session_state["auth_user"] = None


def require_auth(message: str = "Debes iniciar sesion para continuar.") -> str:
    token = get_auth_token()
    if token:
        return token

    if hasattr(st, "switch_page"):
        st.switch_page("pages/0_auth.py")

    st.warning(message)
    if hasattr(st, "page_link"):
        st.page_link("pages/0_auth.py", label="Ir a Auth")
    st.stop()
