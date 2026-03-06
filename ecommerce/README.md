# Ecommerce Monorepo

Proyecto con arquitectura Clean/Hexagonal ligera.

## Servicios en Docker

- `postgres`: base de datos PostgreSQL.
- `fastapi`: API v1 (`/health`, productos, auth, carrito, pedidos).
- `streamlit`: UI cliente que consume la API por HTTP.

Cada servicio corre en su propio contenedor y se conecta por red interna de Docker.

## Requisitos

- Docker + Docker Compose
- Python 3.11+ (solo para ejecución local sin Docker)

## Variables de entorno esperadas

- `DATABASE_URL`
- `JWT_SECRET`
- `API_BASE_URL`
- `ENV`
- `CORS_ORIGINS`

## Levantar stack completo con Docker

```bash
cd ecommerce
docker compose -f docker/docker-compose.yml up --build -d
```

Comprobar servicios:

```bash
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f fastapi
docker compose -f docker/docker-compose.yml logs -f streamlit
```

URLs:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Streamlit: `http://localhost:8501`

Nota: el contenedor `fastapi` ejecuta `alembic upgrade head` en startup antes de iniciar Uvicorn.

## Ejecucion local (sin Docker)

```bash
cd ecommerce
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev]'
```

Migrar DB local:

```bash
alembic -c packages/core/infrastructure/db/migrations/alembic.ini upgrade head
```

API:

```bash
uvicorn apps.FastAPI.app.main:app --reload --host 0.0.0.0 --port 8000
```

UI:

```bash
streamlit run apps/Streamlit/app.py --server.port 8501
```

## Calidad y tests

```bash
ruff format --check .
ruff check .
mypy apps packages
pytest
```
