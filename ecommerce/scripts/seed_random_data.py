from __future__ import annotations

import argparse
import os
import random
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy.exc import OperationalError, SQLAlchemyError


def _load_env_file() -> None:
    if os.getenv("DATABASE_URL"):
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()

if TYPE_CHECKING:
    from packages.core.infrastructure.db.models import ProductModel, UserModel

ADJECTIVES = [
    "Smart",
    "Ultra",
    "Eco",
    "Prime",
    "Compact",
    "Max",
    "Mini",
    "Pro",
]

NOUNS = [
    "Phone",
    "Laptop",
    "Headphones",
    "Mouse",
    "Keyboard",
    "Speaker",
    "Camera",
    "Monitor",
]

DESCRIPTIONS = [
    "Dispositivo ideal para uso diario.",
    "Excelente relacion calidad precio.",
    "Pensado para productividad y entretenimiento.",
    "Ligero, resistente y eficiente.",
    "Version actualizada con mejor rendimiento.",
]

EMAIL_DOMAINS = ["example.com", "mail.com", "demo.local"]


@dataclass(frozen=True, slots=True)
class SeedConfig:
    products: int
    users: int
    user_password: str


def _random_price() -> Decimal:
    value = round(random.uniform(5, 1200), 2)
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _build_product(index: int) -> ProductModel:
    from packages.core.infrastructure.db.models import ProductModel

    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    name = f"{adjective} {noun} {index}"
    description = random.choice(DESCRIPTIONS)
    return ProductModel(
        id=str(uuid4()),
        name=name,
        description=description,
        price=_random_price(),
        stock=random.randint(0, 120),
    )


def _build_user(index: int, password: str) -> UserModel:
    from apps.FastAPI.app.auth_utils import hash_password
    from packages.core.infrastructure.db.models import UserModel

    email = f"user{index}.{random.randint(1000, 9999)}@{random.choice(EMAIL_DOMAINS)}"
    return UserModel(
        id=str(uuid4()),
        email=email,
        hashed_password=hash_password(password),
        is_admin=False,
    )


def seed_data(config: SeedConfig) -> tuple[int, int]:
    _load_env_file()
    from packages.core.infrastructure.db.session import SessionLocal

    session = SessionLocal()
    created_products = 0
    created_users = 0

    try:
        for index in range(1, config.products + 1):
            session.add(_build_product(index=index))
            created_products += 1

        for index in range(1, config.users + 1):
            session.add(_build_user(index=index, password=config.user_password))
            created_users += 1

        session.commit()
        return created_products, created_users
    except OperationalError as exc:
        session.rollback()
        msg = (
            "No se pudo insertar datos porque faltan tablas o la DB no esta disponible. "
            "Ejecuta primero la migracion inicial con alembic upgrade head."
        )
        raise RuntimeError(msg) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise RuntimeError(f"Error insertando datos: {exc}") from exc
    finally:
        session.close()


def _parse_args() -> SeedConfig:
    parser = argparse.ArgumentParser(
        description="Poblar base de datos con objetos aleatorios para desarrollo.",
    )
    parser.add_argument(
        "n",
        nargs="?",
        type=int,
        default=25,
        help="Numero de productos aleatorios a crear (default: 25).",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=5,
        help="Numero de usuarios aleatorios a crear (default: 5).",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="demo12345",
        help="Password base para usuarios creados (default: demo12345).",
    )

    args = parser.parse_args()

    if args.n < 0 or args.users < 0:
        parser.error("Los valores n y --users deben ser >= 0")

    return SeedConfig(
        products=args.n,
        users=args.users,
        user_password=args.password,
    )


def main() -> None:
    config = _parse_args()
    created_products, created_users = seed_data(config)
    print(
        "Seed completado:",
        f"products={created_products}",
        f"users={created_users}",
        f"default_password={config.user_password}",
    )


if __name__ == "__main__":
    main()
