"""HTTP surface for the app's /citations page.

POST /api/pramana/bind · GET /api/pramana/cert/{id} · POST /api/pramana/audit
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from . import certificate as c
from .bind import ExtractionError, bind
from .extract import AskFn
from .schema import Source


class BindRequest(BaseModel):
    claim: str
    citation_raw: str = ""
    source_text: Optional[str] = None  # None = the source could not be located
    source_locator: str = ""
    authority_rank: int = 0
    n_runs: int = 3


def router(ledger_path: Path, ask_fn: AskFn, model: str = "", pubkey: Optional[str] = None) -> APIRouter:
    r = APIRouter(prefix="/api/pramana")

    @r.post("/bind")
    def _bind(req: BindRequest) -> dict:
        src = Source(locator=req.source_locator, authority_rank=req.authority_rank)
        try:
            body, texts = bind(req.claim, req.source_text, ask_fn, citation_raw=req.citation_raw,
                               source=src, n_runs=req.n_runs, model=model)
        except ExtractionError as e:
            raise HTTPException(502, f"the extractor returned no usable decomposition: {e}") from e
        return c.emit(body, c.open_ledger(ledger_path), texts)

    @r.get("/cert/{cid}")
    def _cert(cid: str) -> dict:
        cert = c.find_certificate(ledger_path, cid) if Path(ledger_path).exists() else None
        if cert is None:
            raise HTTPException(404, "no such certificate")
        return cert

    @r.post("/audit")
    def _audit() -> dict:
        if not Path(ledger_path).exists():
            raise HTTPException(404, "no ledger yet")
        return c.audit(ledger_path, pubkey).to_dict()

    return r


def create_app(ledger_path: Path, ask_fn: AskFn, model: str = "", pubkey: Optional[str] = None) -> FastAPI:
    app = FastAPI(title="pramana-bind")
    app.include_router(router(ledger_path, ask_fn, model, pubkey))
    return app
