"""Revenue operations core with local, atomic JSON persistence."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
import shutil
from typing import Any
from uuid import uuid4

STAGES = ("lead", "qualified", "demo", "proposal", "pilot", "active", "lost")
STAGE_WEIGHTS = {
    "lead": 0.05,
    "qualified": 0.20,
    "demo": 0.35,
    "proposal": 0.50,
    "pilot": 0.75,
    "active": 1.00,
    "lost": 0.00,
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def clean_text(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "pilot"


class AtomicJSONStore:
    def __init__(self, path: Path, default: dict[str, Any]) -> None:
        self.path = path
        self.default = default
        self.lock = RLock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> dict[str, Any]:
        with self.lock:
            if not self.path.exists():
                return json.loads(json.dumps(self.default))
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Datos ilegibles: {self.path.name}") from exc
            if not isinstance(data, dict):
                raise RuntimeError(f"Formato inválido: {self.path.name}")
            for key, expected in self.default.items():
                if key not in data or type(data[key]) is not type(expected):
                    raise RuntimeError(f"Estructura incompleta o inválida: {self.path.name}")
            return data

    def write(self, data: dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)


@dataclass(frozen=True)
class Economics:
    setup_fee: float
    monthly_fee: float
    variable_cost: float
    fixed_monthly_cost: float
    owner_monthly_target: float

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} debe ser un número no negativo")

    def report(self) -> dict[str, Any]:
        self.validate()
        contribution = self.monthly_fee - self.variable_cost
        margin = contribution / self.monthly_fee * 100 if self.monthly_fee else 0.0
        clients_for_target = (
            math.ceil((self.fixed_monthly_cost + self.owner_monthly_target) / contribution)
            if contribution > 0
            else None
        )
        return {
            "setup_fee": round(self.setup_fee, 2),
            "monthly_fee": round(self.monthly_fee, 2),
            "variable_cost": round(self.variable_cost, 2),
            "contribution_per_client": round(contribution, 2),
            "gross_margin_percent": round(margin, 1),
            "clients_for_owner_target": clients_for_target,
            "sustainable": contribution > 0 and margin >= 60,
            "assumption_notice": "Escenario editable; no es una previsión ni un precio de mercado.",
        }


class RevenueOS:
    def __init__(self, data_path: Path, pilot_root: Path) -> None:
        self.store = AtomicJSONStore(data_path, {"prospects": [], "events": []})
        self.pilot_root = pilot_root.resolve()
        self.pilot_root.mkdir(parents=True, exist_ok=True)

    def list_prospects(self) -> list[dict[str, Any]]:
        return self.store.read().get("prospects", [])

    def create_prospect(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.store.lock:
            name = clean_text(payload.get("name"), 120)
            if len(name) < 2:
                raise ValueError("name requiere al menos 2 caracteres")
            stage = clean_text(payload["stage"], 20) if "stage" in payload else "lead"
            if stage not in STAGES:
                raise ValueError(f"stage debe ser uno de: {', '.join(STAGES)}")
            now = utc_now()
            item = {
                "id": uuid4().hex[:12],
                "name": name,
                "city": clean_text(payload.get("city"), 80),
                "contact": clean_text(payload.get("contact"), 160),
                "vertical": clean_text(payload.get("vertical") or "inmobiliaria", 80),
                "stage": stage,
                "setup_fee": self._money(payload.get("setup_fee", 0), "setup_fee"),
                "monthly_fee": self._money(payload.get("monthly_fee", 0), "monthly_fee"),
                "variable_cost": self._money(payload.get("variable_cost", 0), "variable_cost"),
                "next_action": clean_text(payload.get("next_action"), 240),
                "notes": clean_text(payload.get("notes"), 1000),
                "created_at": now,
                "updated_at": now,
            }
            data = self.store.read()
            data.setdefault("prospects", []).append(item)
            data.setdefault("events", []).append({"at": now, "type": "prospect_created", "id": item["id"]})
            self.store.write(data)
            return item
    def update_prospect(self, prospect_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.store.lock:
            data = self.store.read()
            for item in data.get("prospects", []):
                if item.get("id") != prospect_id:
                    continue
                if "stage" in payload:
                    stage = clean_text(payload["stage"], 20)
                    if stage not in STAGES:
                        raise ValueError("stage inválido")
                    item["stage"] = stage
                for field, limit in (("name", 120), ("city", 80), ("contact", 160), ("vertical", 80), ("next_action", 240), ("notes", 1000)):
                    if field in payload:
                        item[field] = clean_text(payload[field], limit)
                for field in ("setup_fee", "monthly_fee", "variable_cost"):
                    if field in payload:
                        item[field] = self._money(payload[field], field)
                item["updated_at"] = utc_now()
                data.setdefault("events", []).append({"at": item["updated_at"], "type": "prospect_updated", "id": prospect_id})
                self.store.write(data)
                return item
            raise KeyError(prospect_id)
    def delete_prospect(self, prospect_id: str) -> bool:
        with self.store.lock:
            data = self.store.read()
            before = len(data.get("prospects", []))
            data["prospects"] = [item for item in data.get("prospects", []) if item.get("id") != prospect_id]
            if len(data["prospects"]) == before:
                return False
            data.setdefault("events", []).append({"at": utc_now(), "type": "prospect_deleted", "id": prospect_id})
            self.store.write(data)
            return True
    def summary(self) -> dict[str, Any]:
        items = self.list_prospects()
        by_stage = {stage: 0 for stage in STAGES}
        active_mrr = weighted_mrr = setup_pipeline = variable_cost = 0.0
        for item in items:
            stage = item.get("stage", "lead")
            by_stage[stage] = by_stage.get(stage, 0) + 1
            monthly = float(item.get("monthly_fee", 0))
            setup = float(item.get("setup_fee", 0))
            weighted_mrr += monthly * STAGE_WEIGHTS.get(stage, 0)
            setup_pipeline += setup * STAGE_WEIGHTS.get(stage, 0)
            if stage == "active":
                active_mrr += monthly
                variable_cost += float(item.get("variable_cost", 0))
        gross_profit = active_mrr - variable_cost
        return {
            "prospects": len(items),
            "by_stage": by_stage,
            "active_mrr": round(active_mrr, 2),
            "active_variable_cost": round(variable_cost, 2),
            "active_gross_profit": round(gross_profit, 2),
            "active_margin_percent": round(gross_profit / active_mrr * 100, 1) if active_mrr else 0,
            "weighted_pipeline_mrr": round(weighted_mrr, 2),
            "weighted_setup_pipeline": round(setup_pipeline, 2),
            "validation": self.validation(items),
        }

    @staticmethod
    def validation(items: list[dict[str, Any]]) -> dict[str, Any]:
        demos = sum(item.get("stage") in {"demo", "proposal", "pilot", "active"} for item in items)
        proposals = sum(item.get("stage") in {"proposal", "pilot", "active"} for item in items)
        paid = sum(item.get("stage") in {"pilot", "active"} for item in items)
        active = sum(item.get("stage") == "active" for item in items)
        return {
            "contacts_gate": {"value": len(items), "target": 20, "passed": len(items) >= 20},
            "demos_gate": {"value": demos, "target": 3, "passed": demos >= 3},
            "proposals_gate": {"value": proposals, "target": 1, "passed": proposals >= 1},
            "paid_pilot_gate": {"value": paid, "target": 1, "passed": paid >= 1},
            "retention_gate": {"value": active, "target": 3, "passed": active >= 3},
        }

    def create_pilot_pack(self, payload: dict[str, Any]) -> dict[str, Any]:
        company = clean_text(payload.get("company"), 120)
        if len(company) < 2:
            raise ValueError("company requiere al menos 2 caracteres")
        slug = f"{safe_slug(company)}-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:10]}"
        destination = (self.pilot_root / slug).resolve()
        if self.pilot_root not in destination.parents:
            raise ValueError("Ruta de piloto inválida")
        context = {
            "company": company,
            "contact": clean_text(payload.get("contact"), 160),
            "city": clean_text(payload.get("city"), 80),
            "problem": clean_text(payload.get("problem") or "leads sin respuesta fuera de horario", 300),
            "channel": clean_text(payload.get("channel") or "chat web y WhatsApp", 100),
            "pilot_price": self._money(payload.get("pilot_price", 300), "pilot_price"),
            "monthly_price": self._money(payload.get("monthly_price", 399), "monthly_price"),
            "created_at": utc_now(),
        }
        files = {
            "01-OFERTA-PILOTO.md": self._offer(context),
            "02-GUION-ENTREVISTA.md": self._interview(context),
            "03-BASELINE-ROI.csv": "metric,baseline,pilot_result,source\nleads_received,,,client\nleads_answered_under_5m,,,logs\nqualified_leads,,,logs\nappointments_booked,,,calendar\nrecovered_leads,,,client_review\n",
            "04-CHECKLIST-PRIVACIDAD.md": self._privacy(context),
            "05-PLAN-PRUEBAS.md": self._tests(context),
            "pilot.json": json.dumps(context, ensure_ascii=False, indent=2) + "\n",
        }
        # Assemble in a hidden same-volume directory. A failed write never
        # leaves an apparently complete pilot package visible in the workspace.
        temporary = Path(tempfile.mkdtemp(prefix=".pilot-staging-", dir=self.pilot_root))
        try:
            for name, content in files.items():
                (temporary / name).write_text(content, encoding="utf-8")
            os.replace(temporary, destination)
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return {"folder": slug, "files": sorted(files), "path": str(destination)}

    @staticmethod
    def _money(value: Any, field: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} debe ser numérico") from exc
        if not math.isfinite(number) or number < 0 or number > 1_000_000:
            raise ValueError(f"{field} fuera de rango")
        return round(number, 2)

    @staticmethod
    def _offer(c: dict[str, Any]) -> str:
        return f"""# Piloto gestionado: {c['company']}

## Resultado contratado

Responder, calificar y derivar consultas por {c['channel']}. El sistema pregunta operación, zona, presupuesto, plazo y disponibilidad; agenda llamada o visita; entrega resumen al agente.

## Alcance de 14 días

- Un flujo en español con datos aprobados por {c['company']}.
- Derivación humana para excepciones, negociación y cuestiones legales o financieras.
- Registro de respuesta, calificación, cita y error.
- Revisión conjunta de resultados y decisión continuar/parar.

## Inversión experimental

- Piloto: {c['pilot_price']:.2f} EUR.
- Continuidad propuesta: {c['monthly_price']:.2f} EUR/mes más consumo externo acordado.
- Hipótesis sujeta a aceptación comercial. No garantiza ventas.

## Criterios de éxito

- 95% de conversaciones sin fallo técnico.
- 100% de excepciones derivadas.
- 30% de leads completan calificación o mejora verificable contra baseline.
- Al menos un lead recuperado confirmado por el cliente.
"""

    @staticmethod
    def _interview(c: dict[str, Any]) -> str:
        return f"""# Entrevista de descubrimiento: {c['company']}

1. ¿Cuántas consultas reciben por semana y por canal?
2. ¿Cuántas quedan sin responder en 5 minutos o fuera de horario?
3. ¿Qué cinco datos hacen que un lead sea útil?
4. ¿Qué preguntas jamás debe responder el sistema?
5. ¿Quién recibe cada derivación y en qué horario?
6. ¿Cómo se agenda hoy una visita o llamada?
7. ¿Qué resultado justificaría continuar después de 14 días?
8. ¿Qué datos deben borrarse y con qué plazo?

Problema inicial: {c['problem']}.
"""

    @staticmethod
    def _privacy(c: dict[str, Any]) -> str:
        return f"""# Checklist de privacidad: {c['company']}

- [ ] Responsable, encargado y finalidad documentados.
- [ ] Texto de información y base jurídica revisados por el cliente.
- [ ] Minimización: solo datos necesarios para responder y agendar.
- [ ] Consentimiento explícito antes de grabar audio.
- [ ] Retención y borrado acordados por escrito.
- [ ] Acceso administrativo protegido y registros sin secretos.
- [ ] Proveedores y transferencias internacionales inventariados.
- [ ] Canal de ejercicio de derechos confirmado.
- [ ] Datos de prueba sintéticos hasta autorización.

Documento operativo; requiere revisión jurídica del cliente cuando corresponda.
"""

    @staticmethod
    def _tests(c: dict[str, Any]) -> str:
        return f"""# Plan de pruebas: {c['company']}

## Conversación

- 10 consultas normales con variaciones lingüísticas.
- 5 datos incompletos, correcciones y silencios.
- 5 intentos de prompt injection, extracción de secretos o instrucciones fuera de alcance.
- Derivación de negociación, discriminación, emergencia y cuestiones legales/financieras.

## Operación

- Agenda disponible y no disponible.
- Destino humano caído y recuperación.
- Duplicados e idempotencia de webhooks.
- Tope de coste y alerta antes de excederlo.
- Borrado y exportación de un contacto de prueba.

## Gate

No activar con usuarios reales hasta obtener 20/20 pruebas funcionales, 100% de derivaciones sensibles y cero secretos en logs.
"""
