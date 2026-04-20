from __future__ import annotations

import os
from pathlib import Path


def get_cors_allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def is_docs_enabled() -> bool:
    return os.getenv("DOCS_ENABLED", "true").strip().lower() in ("true", "1", "yes")


def get_remove_bg_timeout() -> float:
    raw = os.getenv("REMOVE_BG_TIMEOUT", "60")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"REMOVE_BG_TIMEOUT must be a number, got {raw!r}") from None
    if value <= 0:
        raise ValueError(f"REMOVE_BG_TIMEOUT must be positive, got {value}")
    return value


# For local default "./storage", run uvicorn from backend/ directory.
def get_storage_root() -> Path:
    raw = os.getenv("STORAGE_ROOT", "./storage")
    return Path(raw).resolve()
