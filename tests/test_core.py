import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from core import AtomicJSONStore, Economics, RevenueOS, safe_slug


@pytest.fixture()
def engine(tmp_path: Path) -> RevenueOS:
    return RevenueOS(tmp_path / "data.json", tmp_path / "pilots")


def test_atomic_store_roundtrip(tmp_path: Path):
    store = AtomicJSONStore(tmp_path / "nested" / "state.json", {"items": []})
    assert store.read() == {"items": []}
    store.write({"items": [{"id": 1}]})
    assert store.read()["items"][0]["id"] == 1


def test_atomic_store_rejects_corruption(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("not-json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Datos ilegibles"):
        AtomicJSONStore(path, {}).read()


def test_create_update_delete_and_summary(engine: RevenueOS):
    item = engine.create_prospect({
        "name": "Inmobiliaria Norte",
        "stage": "pilot",
        "setup_fee": 750,
        "monthly_fee": 400,
        "variable_cost": 50,
    })
    summary = engine.summary()
    assert summary["prospects"] == 1
    assert summary["weighted_pipeline_mrr"] == 300
    assert summary["validation"]["paid_pilot_gate"]["passed"]
    updated = engine.update_prospect(item["id"], {"stage": "active"})
    assert updated["stage"] == "active"
    assert engine.summary()["active_gross_profit"] == 350
    assert engine.delete_prospect(item["id"])
    assert not engine.delete_prospect(item["id"])


@pytest.mark.parametrize("stage", ["invalid", "", "ACTIVE"])
def test_invalid_stage_rejected(engine: RevenueOS, stage: str):
    with pytest.raises(ValueError):
        engine.create_prospect({"name": "Cuenta", "stage": stage})


@pytest.mark.parametrize("value", [-1, float("inf"), "abc"])
def test_invalid_money_rejected(engine: RevenueOS, value):
    with pytest.raises(ValueError):
        engine.create_prospect({"name": "Cuenta", "monthly_fee": value})


def test_economics_calculates_target_and_margin():
    report = Economics(750, 399, 60, 100, 2500).report()
    assert report["contribution_per_client"] == 339
    assert report["gross_margin_percent"] == 85.0
    assert report["clients_for_owner_target"] == 8
    assert report["sustainable"] is True


def test_economics_handles_zero_or_negative_contribution():
    report = Economics(0, 50, 60, 100, 1000).report()
    assert report["clients_for_owner_target"] is None
    assert report["sustainable"] is False


def test_pilot_pack_is_bounded_and_complete(engine: RevenueOS):
    result = engine.create_pilot_pack({"company": "Ática / Inmuebles", "pilot_price": 300})
    folder = Path(result["path"])
    assert folder.parent == engine.pilot_root
    assert len(result["files"]) == 6
    assert (folder / "01-OFERTA-PILOTO.md").exists()
    assert "No garantiza ventas" in (folder / "01-OFERTA-PILOTO.md").read_text(encoding="utf-8")
    assert json.loads((folder / "pilot.json").read_text(encoding="utf-8"))["pilot_price"] == 300


def test_slug_never_contains_traversal():
    slug = safe_slug("../../Mi Empresa\\secreta")
    assert "/" not in slug and "\\" not in slug and ".." not in slug

def test_parallel_creates_do_not_lose_customer_records(engine: RevenueOS):
    """HTTP threads must not lose records between JSON read and replace."""
    def create(i: int):
        return engine.create_prospect({"name": f"Empresa {i}", "stage": "lead"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(create, range(40)))
    persisted = engine.list_prospects()
    assert len(records) == len(persisted) == 40
    assert len({row["id"] for row in persisted}) == 40
    assert len({row["name"] for row in persisted}) == 40
    assert engine.summary()["prospects"] == 40


def test_two_pilot_folders_same_company_do_not_collide(engine: RevenueOS):
    first = engine.create_pilot_pack({"company": "Empresa Repetida"})
    second = engine.create_pilot_pack({"company": "Empresa Repetida"})
    assert first["path"] != second["path"]
    assert Path(first["path"]).is_dir()
    assert Path(second["path"]).is_dir()
    assert len(first["files"]) == len(second["files"]) == 6


def test_partial_local_database_fails_closed_instead_of_resetting_clients(tmp_path: Path):
    state = tmp_path / "broken-state.json"
    original = '{"prospects":[{"id":"customer"}]}'
    state.write_text(original, encoding="utf-8")
    engine = RevenueOS(state, tmp_path / "pilots")
    with pytest.raises(RuntimeError, match="Estructura incompleta"):
        engine.create_prospect({"name": "Nuevo cliente"})
    assert state.read_text(encoding="utf-8") == original


def test_pilot_invalid_price_never_creates_a_folder(engine: RevenueOS):
    before = list(engine.pilot_root.iterdir())
    with pytest.raises(ValueError):
        engine.create_pilot_pack({"company": "Empresa Verificada", "pilot_price": -100})
    assert list(engine.pilot_root.iterdir()) == before


def test_pilot_staging_cleaned_when_a_file_write_fails(engine: RevenueOS, monkeypatch):
    from unittest.mock import patch

    existing = list(engine.pilot_root.iterdir())
    real_write = Path.write_text
    calls = []

    def fails_at_second_write(path, content, *args, **kwargs):
        calls.append(str(path))
        if len(calls) == 2:
            raise OSError("disk interrupted")
        return real_write(path, content, *args, **kwargs)

    with patch.object(Path, "write_text", fails_at_second_write):
        with pytest.raises(OSError, match="disk interrupted"):
            engine.create_pilot_pack({"company": "Empresa Fallida"})
    assert list(engine.pilot_root.iterdir()) == existing


def test_successful_pilot_has_no_staging_folders(engine: RevenueOS):
    result = engine.create_pilot_pack({"company": "Empresa Normal"})
    assert Path(result["path"]).is_dir()
    assert len(list(Path(result["path"]).iterdir())) == 6
    assert not any(p.name.startswith(".pilot-staging-") for p in engine.pilot_root.iterdir())

