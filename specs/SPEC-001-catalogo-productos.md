---
id: SPEC-001
title: Catalogo de productos
status: active
area: catalog
source_paths:
  - ecommerce/apps/FastAPI/app/routers/products.py
  - ecommerce/apps/FastAPI/app/schemas/product.py
  - ecommerce/packages/core/application/use_cases/list_products.py
  - ecommerce/apps/Streamlit/pages/1_catalogo.py
doc_targets:
  - docs/generated/catalogo-productos.md
---

# Catalogo de productos

## Resumen

El catalogo permite consultar productos disponibles desde la API y mostrarlos
en la interfaz Streamlit. Debe soportar listados paginados y datos suficientes
para que el usuario pueda decidir si agrega un producto al carrito.

## Alcance

- Listado de productos desde FastAPI.
- Representacion basica de nombre, precio y stock.
- Consumo desde la pagina de catalogo de Streamlit.
- Casos simples de paginacion o consulta.

## Flujo

1. El usuario abre la pagina de catalogo.
2. Streamlit solicita productos a la API.
3. La API delega la consulta al caso de uso de listado.
4. La respuesta se renderiza como una lista navegable.

## Criterios de aceptacion

- La API expone un endpoint para listar productos.
- La respuesta incluye identificador, nombre, precio y stock.
- La UI muestra un estado util cuando no hay productos.
- Los tests cubren al menos una consulta exitosa y un caso de paginacion.

## Notas para el generador

Generar una pagina de referencia funcional con links a las rutas fuente y una
tabla resumen de campos principales del producto.

