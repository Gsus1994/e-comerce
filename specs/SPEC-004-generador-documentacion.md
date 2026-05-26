---
id: SPEC-004
title: Generador automatico de documentacion
status: draft
area: tooling
source_paths:
  - docs/specs
  - ecommerce/README.md
doc_targets:
  - docs/generated/index.md
  - docs/generated/spec-map.md
---

# Generador automatico de documentacion

## Resumen

La herramienta debe leer specs del repositorio y producir documentacion derivada
que se pueda regenerar cuando cambien las especificaciones o el codigo citado.

## Alcance

- Descubrimiento de archivos `docs/specs/*.md`.
- Lectura de frontmatter y contenido Markdown.
- Validacion minima de campos requeridos.
- Generacion de un indice y paginas por spec.

## Flujo

1. La herramienta busca specs en `docs/specs`.
2. Valida que cada spec tenga `id`, `title`, `status` y `source_paths`.
3. Genera una pagina por spec en `docs/generated`.
4. Genera un indice con links, estado, area y rutas fuente.

## Criterios de aceptacion

- Un spec incompleto produce un error claro.
- La salida generada es determinista.
- Las paginas incluyen fecha de generacion y referencia al spec original.
- Los archivos generados pueden borrarse y reconstruirse desde cero.

## Notas para el generador

Este spec esta pensado como fixture de la propia herramienta. Puede usarse para
validar que el sistema documenta su propio proceso de generacion.

