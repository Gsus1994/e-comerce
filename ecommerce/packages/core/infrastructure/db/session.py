from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///./ecommerce.db"


def _resolve_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_engine_from_url(database_url: str | None = None) -> Engine:
    url = database_url or _resolve_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = create_engine_from_url()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
