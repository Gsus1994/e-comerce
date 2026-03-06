from __future__ import annotations

from typing import Any

from apps.Streamlit.client.api_client import ApiClient, ApiClientError, CartItemPayload
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


_init_state()
client = _get_client()

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

auth_token = str(st.session_state.get("auth_token", ""))

if not auth_token:
    st.warning("Debes iniciar sesion o registrarte para crear el pedido.")
    login_col, register_col = st.columns(2)

    with login_col:
        st.markdown("### Login")
        with st.form("checkout_login_form"):
            login_email = st.text_input("Email", key="checkout_login_email")
            login_password = st.text_input(
                "Password", type="password", key="checkout_login_password"
            )
            login_submit = st.form_submit_button("Iniciar sesion")

        if login_submit:
            try:
                result = client.login(email=login_email, password=login_password)
                st.session_state["auth_token"] = str(result["access_token"])
                st.session_state["auth_user"] = result.get("user")
                st.success("Sesion iniciada")
                st.rerun()
            except ApiClientError as exc:
                st.error(str(exc))

    with register_col:
        st.markdown("### Registro")
        with st.form("checkout_register_form"):
            register_email = st.text_input("Email", key="checkout_register_email")
            register_password = st.text_input(
                "Password (min 8)",
                type="password",
                key="checkout_register_password",
            )
            register_submit = st.form_submit_button("Crear cuenta")

        if register_submit:
            try:
                result = client.register(email=register_email, password=register_password)
                st.session_state["auth_token"] = str(result["access_token"])
                st.session_state["auth_user"] = result.get("user")
                st.success("Cuenta creada y sesion iniciada")
                st.rerun()
            except ApiClientError as exc:
                st.error(str(exc))

    st.stop()

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
