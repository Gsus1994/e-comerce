from __future__ import annotations

from typing import Any

from apps.Streamlit.auth_guard import clear_auth_session, init_session_state
from apps.Streamlit.client.api_client import ApiClient, ApiClientError
from apps.Streamlit.settings import get_settings

import streamlit as st


def _get_client() -> ApiClient:
    return ApiClient(base_url=get_settings().api_base_url)


def _set_auth_session(payload: dict[str, Any]) -> None:
    st.session_state["auth_token"] = str(payload.get("access_token", ""))
    st.session_state["auth_user"] = payload.get("user")


init_session_state()
client = _get_client()

st.title("Auth")
auth_token = str(st.session_state.get("auth_token", ""))
auth_user = st.session_state.get("auth_user")

if auth_token:
    st.success("Sesion activa")
    if isinstance(auth_user, dict) and auth_user.get("email"):
        st.caption(f"Usuario: {auth_user['email']}")

    if st.button("Cerrar sesion"):
        clear_auth_session()
        st.success("Sesion cerrada")
        st.rerun()

col_login, col_register, col_recover = st.columns(3)

with col_login:
    st.subheader("Iniciar sesion")
    with st.form("auth_login_form"):
        login_email = st.text_input("Email", key="auth_login_email")
        login_password = st.text_input("Password", type="password", key="auth_login_password")
        login_submit = st.form_submit_button("Login")

    if login_submit:
        try:
            response = client.login(email=login_email, password=login_password)
            _set_auth_session(response)
            st.success("Sesion iniciada")
            st.rerun()
        except ApiClientError as exc:
            st.error(str(exc))

with col_register:
    st.subheader("Registro")
    with st.form("auth_register_form"):
        register_email = st.text_input("Email", key="auth_register_email")
        register_password = st.text_input(
            "Password (min 8)",
            type="password",
            key="auth_register_password",
        )
        register_password_confirm = st.text_input(
            "Repetir password",
            type="password",
            key="auth_register_password_confirm",
        )
        register_submit = st.form_submit_button("Crear cuenta")

    if register_submit:
        if register_password != register_password_confirm:
            st.error("Las contrasenas no coinciden")
        else:
            try:
                response = client.register(email=register_email, password=register_password)
                _set_auth_session(response)
                st.success("Cuenta creada y sesion iniciada")
                st.rerun()
            except ApiClientError as exc:
                st.error(str(exc))

with col_recover:
    st.subheader("Recuperar password")
    with st.form("auth_recover_form"):
        recover_email = st.text_input("Email", key="auth_recover_email")
        recover_password = st.text_input(
            "Nuevo password (min 8)",
            type="password",
            key="auth_recover_password",
        )
        recover_password_confirm = st.text_input(
            "Repetir nuevo password",
            type="password",
            key="auth_recover_password_confirm",
        )
        recover_submit = st.form_submit_button("Actualizar password")

    if recover_submit:
        if recover_password != recover_password_confirm:
            st.error("Las contrasenas no coinciden")
        else:
            try:
                response = client.recover_password(
                    email=recover_email,
                    new_password=recover_password,
                )
                st.success(str(response.get("message", "Password actualizado")))
            except ApiClientError as exc:
                st.error(str(exc))

st.markdown("### Siguiente paso")
if hasattr(st, "page_link"):
    st.page_link("pages/1_catalogo.py", label="Ir al catalogo")
    st.page_link("pages/2_carrito.py", label="Ir al carrito")
    st.page_link("pages/3_checkout.py", label="Ir a checkout")
    st.page_link("pages/4_mis_pedidos.py", label="Ir a mis pedidos")
