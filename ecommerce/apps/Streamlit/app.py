from __future__ import annotations

import streamlit as st

from apps.Streamlit.auth_guard import init_session_state
from apps.Streamlit.settings import get_settings

st.set_page_config(page_title="Ecommerce MVP", layout="wide")
init_session_state()
settings = get_settings()

st.title("Ecommerce MVP")
st.caption(f"API base URL: {settings.api_base_url}")

cart_size = len(st.session_state["cart"])
authenticated = bool(st.session_state["auth_token"])
auth_user = st.session_state.get("auth_user")

status_col1, status_col2 = st.columns(2)
status_col1.metric("Items en carrito", cart_size)
status_col2.metric("Sesion", "Activa" if authenticated else "No autenticada")
if authenticated and isinstance(auth_user, dict) and auth_user.get("email"):
    st.caption(f"Usuario actual: {auth_user['email']}")

st.markdown("### Navegacion")
if hasattr(st, "page_link"):
    st.page_link("pages/0_auth.py", label="Auth (Login/Registro)")
    st.page_link("pages/1_catalogo.py", label="Catalogo")
    st.page_link("pages/2_carrito.py", label="Carrito")
    st.page_link("pages/3_checkout.py", label="Checkout")
    st.page_link("pages/4_mis_pedidos.py", label="Mis pedidos")
else:
    st.write("Usa el menu lateral de Streamlit para navegar entre paginas.")
