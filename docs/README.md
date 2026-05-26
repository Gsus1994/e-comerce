# Docs

Este directorio contiene ejemplos de documentacion pensados para probar una
herramienta que genere docs actualizadas a partir de specs del proyecto.

## Estructura

- `specs/`: especificaciones fuente en Markdown.
- `specs/README.md`: convenciones minimas para escribir nuevos specs.

## Como usar estos ejemplos

La idea es que cada spec describa una pieza funcional del ecommerce con:

- metadatos faciles de parsear;
- rutas de codigo relacionadas;
- comportamiento esperado;
- criterios de aceptacion;
- posibles salidas documentales.

La herramienta puede recorrer `docs/specs/*.md`, leer el frontmatter y generar
paginas de referencia, changelogs funcionales o documentacion de producto.

