from __future__ import annotations

import os


def get_cors_allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def is_docs_enabled() -> bool:
    return os.getenv("DOCS_ENABLED", "true").strip().lower() in ("true", "1", "yes")


def get_remove_bg_timeout() -> float:
    raw = os.getenv("REMOVE_BG_TIMEOUT", "30")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"REMOVE_BG_TIMEOUT must be a number, got {raw!r}") from None
    if value <= 0:
        raise ValueError(f"REMOVE_BG_TIMEOUT must be positive, got {value}")
    return value
