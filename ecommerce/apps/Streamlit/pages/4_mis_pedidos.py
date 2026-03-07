from __future__ import annotations

import streamlit as st

from apps.Streamlit.auth_guard import clear_auth_session, init_session_state, require_auth
from apps.Streamlit.client.api_client import ApiClient, ApiClientError
from apps.Streamlit.settings import get_settings


def _get_client() -> ApiClient:
    return ApiClient(base_url=get_settings().api_base_url)


init_session_state()
client = _get_client()

st.title("Mis pedidos")
auth_token = require_auth("Debes iniciar sesion para ver tus pedidos.")

if st.button("Cerrar sesion"):
    clear_auth_session()
    st.rerun()

try:
    orders = client.list_my_orders(token=auth_token)
except ApiClientError as exc:
    if exc.status_code == 401:
        clear_auth_session()
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
