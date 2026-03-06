from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    api_base_url: str = "http://localhost:8000"


def get_settings() -> Settings:
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    return Settings(api_base_url=base_url)
