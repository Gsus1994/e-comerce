from __future__ import annotations

import streamlit as st
from apps.Streamlit.settings import get_settings


def init_session_state() -> None:
    st.session_state.setdefault("cart", {})
    st.session_state.setdefault("auth_token", "")
    st.session_state.setdefault("auth_user", None)
    st.session_state.setdefault("cart_validation", None)
    st.session_state.setdefault("last_order", None)


st.set_page_config(page_title="Ecommerce MVP", layout="wide")
init_session_state()
settings = get_settings()

st.title("Ecommerce MVP")
st.caption(f"API base URL: {settings.api_base_url}")

cart_size = len(st.session_state["cart"])
authenticated = bool(st.session_state["auth_token"])

status_col1, status_col2 = st.columns(2)
status_col1.metric("Items en carrito", cart_size)
status_col2.metric("Sesion", "Activa" if authenticated else "No autenticada")

st.markdown("### Navegacion")
if hasattr(st, "page_link"):
    st.page_link("pages/1_catalogo.py", label="Catalogo")
    st.page_link("pages/2_carrito.py", label="Carrito")
    st.page_link("pages/3_checkout.py", label="Checkout")
    st.page_link("pages/4_mis_pedidos.py", label="Mis pedidos")
else:
    st.write("Usa el menu lateral de Streamlit para navegar entre paginas.")
