import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def load_app(tmp_path: Path, monkeypatch, key: str = ""):
    monkeypatch.setenv("LEGACY_DATA_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("LEGACY_PILOT_ROOT", str(tmp_path / "pilots"))
    if key:
        monkeypatch.setenv("ADMIN_API_KEY", key)
    else:
        monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    import app
    return importlib.reload(app)


def test_health_and_dashboard(tmp_path, monkeypatch):
    module = load_app(tmp_path, monkeypatch)
    client = TestClient(module.app)
    assert client.get("/api/health").json()["status"] == "ok"
    page = client.get("/")
    assert page.status_code == 200
    assert "Legacy Revenue OS" in page.text
    assert page.headers["x-frame-options"] == "DENY"
    assert page.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert page.headers["cache-control"] == "no-store"
    assert "@media(max-width:580px)" in page.text
    assert "prefers-reduced-motion" in page.text


def test_prospect_lifecycle(tmp_path, monkeypatch):
    module = load_app(tmp_path, monkeypatch)
    client = TestClient(module.app)
    created = client.post("/api/prospects", json={"name": "Casa Uno", "monthly_fee": 399}).json()
    assert client.get("/api/summary").json()["prospects"] == 1
    assert client.patch(f"/api/prospects/{created['id']}", json={"stage": "active"}).json()["stage"] == "active"
    assert client.delete(f"/api/prospects/{created['id']}").status_code == 204
    assert client.delete(f"/api/prospects/{created['id']}").status_code == 404


def test_admin_key_protects_mutating_and_read_routes(tmp_path, monkeypatch):
    module = load_app(tmp_path, monkeypatch, "secret-test-key")
    client = TestClient(module.app)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/prospects").status_code == 401
    assert client.get("/api/prospects", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert client.get("/api/prospects", headers={"X-Admin-Key": "secret-test-key"}).status_code == 200


def test_validation_and_economics(tmp_path, monkeypatch):
    module = load_app(tmp_path, monkeypatch)
    client = TestClient(module.app)
    assert client.post("/api/prospects", json={"name": "x"}).status_code == 422
    assert client.post("/api/prospects", json={"name": "Cuenta", "stage": "bad"}).status_code == 422
    report = client.post("/api/economics", json={"monthly_fee": 399, "variable_cost": 60}).json()
    assert report["gross_margin_percent"] == 85.0


def test_pilot_pack_endpoint(tmp_path, monkeypatch):
    module = load_app(tmp_path, monkeypatch)
    client = TestClient(module.app)
    result = client.post("/api/pilots", json={"company": "Agencia Centro"})
    assert result.status_code == 201
    body = result.json()
    assert len(body["files"]) == 6
    assert Path(body["path"]).is_dir()
