# Specs

Estos specs son ejemplos ligeros para alimentar un generador automatico de
documentacion. No intentan cubrir todo el proyecto; solo dan formas distintas de
entrada para probar parsing, agrupacion y renderizado.

## Convenciones

Cada spec usa Markdown con frontmatter YAML:

```yaml
---
id: SPEC-000
title: Nombre corto
status: draft
area: catalog
source_paths:
  - ecommerce/apps/FastAPI/app/routers/example.py
doc_targets:
  - docs/generated/example.md
---
```

Secciones sugeridas:

- `Resumen`
- `Alcance`
- `Flujo`
- `Criterios de aceptacion`
- `Notas para el generador`

## Estados de ejemplo

- `draft`: idea o comportamiento en revision.
- `active`: comportamiento esperado actualmente.
- `deprecated`: comportamiento que deberia desaparecer.

