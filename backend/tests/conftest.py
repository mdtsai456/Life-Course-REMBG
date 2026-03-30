"""Shared fixtures for backend tests.

Uses sys.modules patching instead of simple @patch because rembg is imported
at module level in main.py. We inject the mock before app.main is imported.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


_APP_MODULES = [
    "app.main",
    "app.config",
    "app.routes.images",
]


def _cleanup_modules() -> None:
    """Remove cached app modules so the next import gets a fresh copy."""
    for mod in _APP_MODULES:
        sys.modules.pop(mod, None)


def _rembg_sys_modules_patch(mock_rembg: MagicMock) -> dict[str, MagicMock]:
    """Return sys.modules patch dict: only rembg is mocked."""
    return {"rembg": mock_rembg}


@pytest.fixture()
def client():
    """Yield a TestClient with rembg mocked out."""
    mock_session = MagicMock(name="rembg_session")
    mock_rembg = MagicMock()
    mock_rembg.new_session = MagicMock(return_value=mock_session)
    mock_rembg.remove = MagicMock()

    patches = _rembg_sys_modules_patch(mock_rembg)

    saved = {m: sys.modules[m] for m in _APP_MODULES if m in sys.modules}

    with patch.dict(sys.modules, patches):
        _cleanup_modules()

        from app.main import app

        with TestClient(app) as c:
            yield c

        _cleanup_modules()

    for mod, orig in saved.items():
        sys.modules[mod] = orig
        parts = mod.rsplit(".", 1)
        if len(parts) == 2 and parts[0] in sys.modules:
            setattr(sys.modules[parts[0]], parts[1], orig)
