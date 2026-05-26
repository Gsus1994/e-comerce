---
id: SPEC-002
title: Autenticacion, carrito y checkout
status: active
area: checkout
source_paths:
  - ecommerce/apps/FastAPI/app/routers/auth.py
  - ecommerce/apps/FastAPI/app/routers/cart.py
  - ecommerce/apps/FastAPI/app/routers/orders.py
  - ecommerce/apps/Streamlit/pages/0_auth.py
  - ecommerce/apps/Streamlit/pages/2_carrito.py
  - ecommerce/apps/Streamlit/pages/3_checkout.py
doc_targets:
  - docs/generated/checkout.md
---

# Autenticacion, carrito y checkout

## Resumen

El flujo de compra requiere que el usuario se autentique, agregue productos al
carrito y confirme un pedido. Este spec sirve como ejemplo de una funcionalidad
transversal que toca API, UI y dominio.

## Alcance

- Inicio de sesion y uso de token.
- Agregado de productos al carrito.
- Revision del carrito antes de comprar.
- Creacion de pedido desde el checkout.

## Flujo

1. El usuario inicia sesion.
2. La UI conserva el token para llamadas posteriores.
3. El usuario agrega productos al carrito desde catalogo.
4. El usuario revisa cantidades e importe aproximado.
5. El checkout crea un pedido y vacia o actualiza el carrito segun corresponda.

## Criterios de aceptacion

- Los endpoints protegidos rechazan solicitudes sin credenciales validas.
- El carrito mantiene los productos agregados durante la sesion del usuario.
- El checkout crea un pedido con lineas, cantidades y totales consistentes.
- La UI muestra errores comprensibles cuando la API rechaza una accion.

## Notas para el generador

Generar un diagrama textual del flujo y una lista de endpoints involucrados. Si
la herramienta detecta tests relacionados, anexarlos como evidencia.

