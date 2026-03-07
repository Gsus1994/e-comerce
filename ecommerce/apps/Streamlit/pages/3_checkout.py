from __future__ import annotations

from typing import Any

import streamlit as st

from apps.Streamlit.auth_guard import init_session_state, require_auth
from apps.Streamlit.client.api_client import ApiClient, ApiClientError, CartItemPayload
from apps.Streamlit.settings import get_settings


def _get_client() -> ApiClient:
    return ApiClient(base_url=get_settings().api_base_url)


def _cart_payload(cart: dict[str, dict[str, Any]]) -> list[CartItemPayload]:
    payload: list[CartItemPayload] = []
    for item in cart.values():
        qty = int(item["qty"])
        if qty <= 0:
            continue
        payload.append(
            CartItemPayload(
                product_id=str(item["product_id"]),
                qty=qty,
            ),
        )
    return payload


init_session_state()
client = _get_client()
auth_token = require_auth("Debes iniciar sesion para crear pedidos.")

st.title("Checkout")

cart: dict[str, dict[str, Any]] = st.session_state["cart"]
if not cart:
    st.info("No hay items en el carrito. Agrega productos desde el catalogo.")
    st.stop()

st.subheader("Resumen")
items_payload = _cart_payload(cart)
if not items_payload:
    st.warning("El carrito no tiene cantidades validas.")
    st.stop()

for item in cart.values():
    if int(item["qty"]) <= 0:
        continue
    subtotal = float(item["price"]) * int(item["qty"])
    st.write(f"- {item['name']} x {item['qty']} = ${subtotal:.2f}")

total = sum(
    float(item["price"]) * int(item["qty"]) for item in cart.values() if int(item["qty"]) > 0
)
st.metric("Total", f"${total:.2f}")

current_user = st.session_state.get("auth_user")
if isinstance(current_user, dict) and current_user.get("email"):
    st.caption(f"Sesion activa: {current_user['email']}")

if st.button("Crear pedido", type="primary"):
    try:
        order = client.create_order(items=items_payload, token=auth_token)
        st.session_state["last_order"] = order
        st.session_state["cart"] = {}
        st.session_state["cart_validation"] = None
        st.success("Pedido creado correctamente")
        st.json(order)
    except ApiClientError as exc:
        if exc.status_code == 401:
            st.session_state["auth_token"] = ""
            st.session_state["auth_user"] = None
        st.error(str(exc))

last_order = st.session_state.get("last_order")
if isinstance(last_order, dict) and last_order:
    st.subheader("Ultimo pedido")
    st.json(last_order)
