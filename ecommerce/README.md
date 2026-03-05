# Ecommerce Monorepo (Bootstrap)

Bootstrap inicial del repositorio con arquitectura Clean/Hexagonal ligera.  
En esta iteracion solo hay estructura, tooling, CI y placeholders ejecutables.

## Requisitos

- Python 3.11+
- Docker + Docker Compose

## Estructura

```text
ecommerce/
  apps/
    FastAPI/
    Streamlit/
  packages/
    core/
  scripts/
  docker/
```

## Instalacion local

```bash
cd ecommerce
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev]'
pre-commit install
```

## Variables de entorno

```bash
cp .env.example .env
```

## Levantar Postgres (dev)

```bash
cd ecommerce
docker compose -f docker/docker-compose.yml up -d
```

## Ejecutar API (placeholder)

```bash
cd ecommerce
uvicorn apps.FastAPI.app.main:app --reload --host 0.0.0.0 --port 8000
```

Healthcheck:

```bash
curl http://localhost:8000/health
```

## Ejecutar UI (placeholder)

```bash
cd ecommerce
streamlit run apps/Streamlit/app.py --server.port 8501
```

## Calidad y tests

```bash
cd ecommerce
ruff format --check .
ruff check .
mypy apps packages
pytest
```

## CI

GitHub Actions ejecuta lint, typecheck y tests en cada push/pull request.
