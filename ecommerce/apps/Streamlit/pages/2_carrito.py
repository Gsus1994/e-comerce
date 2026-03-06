from __future__ import annotations

from typing import Any

from apps.Streamlit.auth_guard import init_session_state, require_auth
from apps.Streamlit.client.api_client import ApiClient, ApiClientError, CartItemPayload
from apps.Streamlit.settings import get_settings

import streamlit as st


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
require_auth("Debes iniciar sesion para gestionar el carrito.")
client = _get_client()
cart: dict[str, dict[str, Any]] = st.session_state["cart"]

st.title("Carrito")

if not cart:
    st.info("Tu carrito esta vacio. Ve al catalogo para agregar productos.")
    st.stop()

st.subheader("Items")
for product_id, item in cart.items():
    with st.container(border=True):
        st.write(f"**{item['name']}**")
        st.caption(f"Precio unitario: ${float(item['price']):.2f}")
        qty = st.number_input(
            f"Cantidad para {item['name']}",
            min_value=0,
            max_value=max(0, int(item.get("stock", 0))),
            value=int(item["qty"]),
            step=1,
            key=f"cart_qty_{product_id}",
        )
        item["qty"] = int(qty)

col_update, col_validate = st.columns(2)
if col_update.button("Actualizar carrito"):
    to_remove = [pid for pid, data in cart.items() if int(data["qty"]) <= 0]
    for pid in to_remove:
        del cart[pid]
    st.session_state["cart_validation"] = None
    st.success("Carrito actualizado")
    st.rerun()

if col_validate.button("Validar carrito"):
    try:
        payload = _cart_payload(cart)
        if not payload:
            st.warning("No hay items validos para validar.")
        else:
            validation = client.validate_cart(items=payload)
            st.session_state["cart_validation"] = validation
            st.success("Carrito validado correctamente")
    except ApiClientError as exc:
        st.error(str(exc))

local_total = sum(float(item["price"]) * int(item["qty"]) for item in cart.values())
st.metric("Total local estimado", f"${local_total:.2f}")

validation_result = st.session_state.get("cart_validation")
if validation_result:
    st.subheader("Resultado validacion API")
    st.json(validation_result)
