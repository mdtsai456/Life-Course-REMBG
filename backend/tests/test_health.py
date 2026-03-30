"""Tests for GET /health endpoint."""

from __future__ import annotations


class TestHealth:
    def test_health_returns_ok(self, client):
        """rembg loaded → 200 with status=ok."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["checks"]["rembg"] is True
        assert list(data["checks"].keys()) == ["rembg"]

    def test_health_missing_rembg(self, client):
        """rembg_session missing → 503."""
        saved = client.app.state.rembg_session
        del client.app.state.rembg_session
        try:
            resp = client.get("/health")
            assert resp.status_code == 503
            data = resp.json()
            assert data["status"] == "loading"
            assert data["checks"]["rembg"] is False
            assert list(data["checks"].keys()) == ["rembg"]
        finally:
            client.app.state.rembg_session = saved
