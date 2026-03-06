from __future__ import annotations

from typing import Any

from apps.Streamlit.auth_guard import init_session_state, require_auth
from apps.Streamlit.client.api_client import ApiClient, ApiClientError
from apps.Streamlit.settings import get_settings

import streamlit as st


def _get_client() -> ApiClient:
    return ApiClient(base_url=get_settings().api_base_url)


def _add_to_cart(product: dict[str, Any], qty: int) -> None:
    product_id = str(product["id"])
    current_cart: dict[str, dict[str, Any]] = st.session_state["cart"]
    current_item = current_cart.get(product_id)
    current_qty = int(current_item["qty"]) if current_item else 0

    stock = int(product["stock"])
    target_qty = min(current_qty + qty, stock)

    current_cart[product_id] = {
        "product_id": product_id,
        "name": str(product["name"]),
        "price": float(product["price"]),
        "stock": stock,
        "qty": target_qty,
    }

    st.session_state["cart_validation"] = None


init_session_state()
require_auth("Debes iniciar sesion para ver el catalogo.")
client = _get_client()

st.title("Catalogo")
search_query = st.text_input("Buscar producto", placeholder="Nombre o descripcion")

try:
    response = client.get_products(page=1, size=50, q=search_query.strip() or None)
except ApiClientError as exc:
    st.error(str(exc))
    st.stop()

products = response.get("items", [])
st.caption(f"Productos encontrados: {len(products)}")

for product in products:
    product_id = str(product["id"])
    with st.container(border=True):
        st.subheader(str(product["name"]))
        st.write(str(product["description"]))

        col_price, col_stock, col_qty, col_action = st.columns([1, 1, 1, 1.5])
        col_price.metric("Precio", f"${float(product['price']):.2f}")
        col_stock.metric("Stock", int(product["stock"]))

        qty = int(
            col_qty.number_input(
                "Cantidad",
                min_value=1,
                max_value=max(1, int(product["stock"])),
                value=1,
                step=1,
                key=f"qty_{product_id}",
            ),
        )

        if col_action.button("Anadir al carrito", key=f"add_{product_id}"):
            _add_to_cart(product, qty)
            st.success(f"{product['name']} agregado al carrito")

cart_items = st.session_state["cart"]
st.info(f"Items en carrito: {len(cart_items)}")
