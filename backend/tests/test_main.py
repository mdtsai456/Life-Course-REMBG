from __future__ import annotations

import json

import pytest

import app.main as main


@pytest.mark.asyncio
async def test_health_returns_503_when_storage_root_lookup_fails(monkeypatch):
    def raise_storage_error():
        raise OSError("boom")

    monkeypatch.setattr(main, "get_storage_root", raise_storage_error)
    monkeypatch.setattr(main.app.state, "rembg_session", object(), raising=False)
    monkeypatch.setattr(main.app.state, "model_load_seconds", 1.2, raising=False)

    response = await main.health()
    payload = json.loads(response.body)

    assert response.status_code == 503
    assert payload["status"] == "unhealthy"
    assert payload["checks"] == {"rembg": True, "storage_writable": False}
    assert payload["model_loaded_in_s"] == 1.2
