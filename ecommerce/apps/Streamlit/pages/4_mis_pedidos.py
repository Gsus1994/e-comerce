from __future__ import annotations

from apps.Streamlit.client.api_client import ApiClient, ApiClientError
from apps.Streamlit.settings import get_settings

import streamlit as st


def _init_state() -> None:
    st.session_state.setdefault("cart", {})
    st.session_state.setdefault("auth_token", "")
    st.session_state.setdefault("auth_user", None)
    st.session_state.setdefault("cart_validation", None)
    st.session_state.setdefault("last_order", None)


def _get_client() -> ApiClient:
    return ApiClient(base_url=get_settings().api_base_url)


_init_state()
client = _get_client()

st.title("Mis pedidos")
auth_token = str(st.session_state.get("auth_token", ""))

if not auth_token:
    st.warning("Debes iniciar sesion para ver tus pedidos.")

    with st.form("orders_login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Iniciar sesion")

    if submitted:
        try:
            result = client.login(email=email, password=password)
            st.session_state["auth_token"] = str(result["access_token"])
            st.session_state["auth_user"] = result.get("user")
            st.success("Sesion iniciada")
            st.rerun()
        except ApiClientError as exc:
            st.error(str(exc))
    st.stop()

if st.button("Cerrar sesion"):
    st.session_state["auth_token"] = ""
    st.session_state["auth_user"] = None
    st.rerun()

try:
    orders = client.list_my_orders(token=auth_token)
except ApiClientError as exc:
    if exc.status_code == 401:
        st.session_state["auth_token"] = ""
        st.session_state["auth_user"] = None
    st.error(str(exc))
    st.stop()

if not orders:
    st.info("Aun no tienes pedidos.")
    st.stop()

for order in orders:
    with st.container(border=True):
        st.subheader(f"Pedido {order.get('id', '-')}")
        st.caption(f"Estado: {order.get('status', '-')}")
        st.caption(f"Fecha: {order.get('created_at', '-')}")
        st.metric("Total", f"${float(order.get('total', 0)):.2f}")

        items = order.get("items", [])
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                unit_price = float(item.get("unit_price", 0))
                st.write(f"- {item.get('product_id')} x {item.get('qty')} @ ${unit_price:.2f}")
