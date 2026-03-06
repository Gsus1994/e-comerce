FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY scripts ./scripts
COPY docker ./docker

RUN pip install --upgrade pip \
    && pip install -e .

EXPOSE 8000

CMD ["/bin/sh", "-c", "alembic -c packages/core/infrastructure/db/migrations/alembic.ini upgrade head && uvicorn apps.FastAPI.app.main:app --host 0.0.0.0 --port 8000"]
