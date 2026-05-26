---
id: SPEC-003
title: Contratos basicos de API
status: draft
area: api
source_paths:
  - ecommerce/apps/FastAPI/app/main.py
  - ecommerce/apps/FastAPI/app/deps.py
  - ecommerce/apps/FastAPI/app/schemas/user.py
  - ecommerce/apps/FastAPI/app/schemas/order.py
  - ecommerce/apps/FastAPI/tests/test_validation_contracts.py
doc_targets:
  - docs/generated/contratos-api.md
---

# Contratos basicos de API

## Resumen

La API debe mantener contratos estables para que la UI y clientes externos no
dependan de detalles internos del dominio. Este spec es un ejemplo para probar
documentacion orientada a integraciones.

## Alcance

- Health check.
- Respuestas de error validables.
- Esquemas publicos de usuario, producto y pedido.
- Reglas de autenticacion aplicadas desde dependencias compartidas.

## Flujo

1. El cliente llama a un endpoint publico o protegido.
2. FastAPI valida parametros, body y credenciales.
3. El router responde con un esquema serializable.
4. Los errores siguen una forma consistente para facilitar depuracion.

## Criterios de aceptacion

- Los errores de validacion usan codigos HTTP adecuados.
- Los schemas publicos no filtran datos sensibles.
- El health check permite comprobar disponibilidad sin credenciales.
- Los tests de contrato fallan si cambia una respuesta publica importante.

## Notas para el generador

Extraer una tabla de endpoints desde los routers y cruzarla con los schemas
citados en `source_paths`.

