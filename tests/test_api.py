from __future__ import annotations

from fastapi.testclient import TestClient

from src.server import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
