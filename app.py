"""FastAPI application for the local Legacy Revenue OS."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core import Economics, RevenueOS

ROOT = Path(__file__).resolve().parent
DATA_PATH = Path(os.getenv("LEGACY_DATA_PATH", ROOT / "data" / "revenue.json"))
PILOT_ROOT = Path(os.getenv("LEGACY_PILOT_ROOT", ROOT / "pilots"))
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "").strip()
engine = RevenueOS(DATA_PATH, PILOT_ROOT)

app = FastAPI(title="Legacy Revenue OS", version="1.0.0", docs_url="/api/docs")


@app.middleware("http")
async def security_headers(request: Any, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    # CRM responses contain client contacts and commercially sensitive numbers.
    # Do not cache them in the browser, a proxy or an intermediate gateway.
    if request.url.path == "/" or request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Fail closed: a missing secret must never disable protection on local APIs."""
    if not ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_KEY must be configured before accessing client data",
        )
    if not (x_admin_key and secrets.compare_digest(x_admin_key, ADMIN_KEY)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin key required")


class ProspectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(default="", max_length=80)
    contact: str = Field(default="", max_length=160)
    vertical: str = Field(default="inmobiliaria", max_length=80)
    stage: str = "lead"
    setup_fee: float = Field(default=0, ge=0, le=1_000_000)
    monthly_fee: float = Field(default=0, ge=0, le=1_000_000)
    variable_cost: float = Field(default=0, ge=0, le=1_000_000)
    next_action: str = Field(default="", max_length=240)
    notes: str = Field(default="", max_length=1000)


class ProspectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    city: str | None = Field(default=None, max_length=80)
    contact: str | None = Field(default=None, max_length=160)
    vertical: str | None = Field(default=None, max_length=80)
    stage: str | None = None
    setup_fee: float | None = Field(default=None, ge=0, le=1_000_000)
    monthly_fee: float | None = Field(default=None, ge=0, le=1_000_000)
    variable_cost: float | None = Field(default=None, ge=0, le=1_000_000)
    next_action: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=1000)


class EconomicsRequest(BaseModel):
    setup_fee: float = Field(default=750, ge=0)
    monthly_fee: float = Field(default=399, ge=0)
    variable_cost: float = Field(default=60, ge=0)
    fixed_monthly_cost: float = Field(default=100, ge=0)
    owner_monthly_target: float = Field(default=2500, ge=0)


class PilotRequest(BaseModel):
    company: str = Field(min_length=2, max_length=120)
    contact: str = Field(default="", max_length=160)
    city: str = Field(default="", max_length=80)
    problem: str = Field(default="", max_length=300)
    channel: str = Field(default="chat web y WhatsApp", max_length=100)
    pilot_price: float = Field(default=300, ge=0, le=1_000_000)
    monthly_price: float = Field(default=399, ge=0, le=1_000_000)


@app.exception_handler(ValueError)
async def value_error_handler(_request: Any, exc: ValueError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(ROOT / "dashboard" / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok" if ADMIN_KEY else "setup_required", "service": "legacy-revenue-os", "admin_protected": True, "ready": bool(ADMIN_KEY)}


@app.get("/api/prospects", dependencies=[Depends(require_admin)])
def prospects() -> list[dict[str, Any]]:
    return engine.list_prospects()


@app.post("/api/prospects", status_code=201, dependencies=[Depends(require_admin)])
def create_prospect(payload: ProspectCreate) -> dict[str, Any]:
    return engine.create_prospect(payload.model_dump())


@app.patch("/api/prospects/{prospect_id}", dependencies=[Depends(require_admin)])
def update_prospect(prospect_id: str, payload: ProspectUpdate) -> dict[str, Any]:
    try:
        return engine.update_prospect(prospect_id, payload.model_dump(exclude_none=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Prospect not found") from exc


@app.delete("/api/prospects/{prospect_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_prospect(prospect_id: str) -> None:
    if not engine.delete_prospect(prospect_id):
        raise HTTPException(status_code=404, detail="Prospect not found")


@app.get("/api/summary", dependencies=[Depends(require_admin)])
def summary() -> dict[str, Any]:
    return engine.summary()


@app.post("/api/economics", dependencies=[Depends(require_admin)])
def economics(payload: EconomicsRequest) -> dict[str, Any]:
    return Economics(**payload.model_dump()).report()


@app.post("/api/pilots", status_code=201, dependencies=[Depends(require_admin)])
def pilot(payload: PilotRequest) -> dict[str, Any]:
    return engine.create_pilot_pack(payload.model_dump())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8091, reload=False)
