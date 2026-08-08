import json
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
