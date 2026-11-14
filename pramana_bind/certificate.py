"""Pramana certificates: emit to the hash-chained ledger (pre-existing
``pravrudhi_kernel.ledger``), sign the chain head with Ed25519, and audit.

``audit`` calls no model. It recomputes the hash chain, checks the signature
on the head, re-runs ``locate_quote`` on every quote against the hashed source
text, and re-derives the verdict and score from the certificate's own world.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pravrudhi_kernel.ledger import LedgerWriter, canonicalize, verify
from pravrudhi_kernel.ledger.verify import iter_events

from .ground import ground, ground_defeaters
from .schema import Avayava, Defeater, Source
from .score import pbs
from .verdict import derive_full
from .world import build_world

KERNEL_RELEASE = "0.1.0"
PAYLOAD_KIND = "pramana_certificate"
CONTEXT = ["https://www.w3.org/ns/credentials/v2", {"pramana": "urn:pramana:v1#"}]


def _pkg(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def _own_commit() -> str:
    here = Path(__file__).resolve().parent.parent
    p = subprocess.run(["git", "-C", str(here), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else "uncommitted"


def cert_id(body: dict[str, Any]) -> str:
    core = {k: v for k, v in body.items() if k != "id"}
    return "urn:pramana:cert:" + hashlib.sha256(canonicalize(core).encode("utf-8")).hexdigest()


def make_body(subject: dict, source: Source, avayava: Avayava, defeaters: list[Defeater],
              text_hashes: dict[str, str], ground_reasons: dict[str, str], lam: float,
              extraction: dict, lean: Optional[dict] = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "@context": CONTEXT,
        "type": "PramanaCertificate",
        "subject": subject,
        "source": source.model_dump(mode="json"),
        "texts": text_hashes,  # source_id -> sha256 of the exact text quotes were located in
        "avayava": avayava.model_dump(mode="json"),
        "defeaters": [d.model_dump(mode="json") for d in defeaters],
        "ground_reasons": ground_reasons,
        "checks": {
            "quote_locator": f"pravrudhi.application.nyaya_quote.locate_quote@pravrudhi-{_pkg('pravrudhi')}",
            "verdict_fn": f"pramana_bind.verdict.derive_full@{_own_commit()}",
            "pbs_lambda": lam,
            # The Lean deciders work on closed worlds; they are run by
            # crosscheck_closed, not per certificate. Never claim otherwise.
            "lean": lean or {"ran": False},
        },
        "extraction": extraction,
    }
    body["id"] = cert_id(body)
    return body


# ----------------------------------------------------------------- ledger

def sources_dir(ledger_path: Path) -> Path:
    return Path(ledger_path).parent / "sources"


def emit(body: dict[str, Any], ledger: LedgerWriter, texts: Optional[dict[str, str]] = None) -> dict[str, Any]:
    """Append the certificate; store each quoted text content-addressed beside
    the ledger so an auditor can re-locate the quotes. Returns the certificate
    with its ledger envelope (seq, t, prev_hash, this_hash)."""
    d = sources_dir(ledger.path)
    for sha, text in (texts or {}).items():
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != sha:
            raise ValueError(f"text does not match its hash {sha}")
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{sha}.txt").write_bytes(text.encode("utf-8"))
    ev = ledger.append("audit", "auditor", {"kind": PAYLOAD_KIND, "severity": "info", "certificate": body},
                       epoch=0, night=0)
    return {**body, "seq": ev.seq, "t": ev.t, "prev_hash": ev.prev_hash, "this_hash": ev.this_hash}


def open_ledger(path: Path) -> LedgerWriter:
    return LedgerWriter.open(Path(path), KERNEL_RELEASE)


def find_certificate(ledger_path: Path, cid: str) -> Optional[dict[str, Any]]:
    for ev in iter_events(Path(ledger_path)):
        c = ev.payload.get("certificate") if ev.payload.get("kind") == PAYLOAD_KIND else None
        if c and c.get("id") == cid:
            out = {**c, "seq": ev.seq, "t": ev.t, "prev_hash": ev.prev_hash, "this_hash": ev.this_hash}
            sig = read_signature(ledger_path)
            if sig:
                out["proof"] = sig
            return out
    return None


# ---------------------------------------------------------------- signing

def generate_key(path: Path) -> str:
    """Write a new Ed25519 private key (base64 raw, mode 0600); return the public key (base64)."""
    key = Ed25519PrivateKey.generate()
    raw = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                            serialization.NoEncryption())
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(base64.b64encode(raw) + b"\n")
    return public_key_b64(key)


def load_key(path: Path) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(Path(path).read_text().strip()))


def public_key_b64(key: Ed25519PrivateKey) -> str:
    return base64.b64encode(key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()


def sig_path(ledger_path: Path) -> Path:
    p = Path(ledger_path)
    return p.with_suffix(p.suffix + ".sig.json")


def read_signature(ledger_path: Path) -> Optional[dict[str, Any]]:
    p = sig_path(ledger_path)
    return json.loads(p.read_text()) if p.exists() else None


def sign_head(ledger_path: Path, key: Ed25519PrivateKey) -> dict[str, Any]:
    """Sign the current chain head. Because every hash covers its predecessor,
    one signature over the head attributes the whole ledger up to that point
    (the same idea as a signed tree head)."""
    res = verify(Path(ledger_path))
    if not res.ok:
        raise ValueError(f"refusing to sign a broken chain: {res.reason} at seq {res.first_bad_seq}")
    proof = {
        "type": "Ed25519", "public_key": public_key_b64(key), "signed_over": "this_hash",
        "seq": res.n - 1, "this_hash": res.head_hash,
        "signature": base64.b64encode(key.sign(bytes.fromhex(res.head_hash))).decode(),
    }
    sig_path(ledger_path).write_text(json.dumps(proof, indent=1) + "\n")
    return proof


# ------------------------------------------------------------------ audit

@dataclass
class Step:
    step: str
    ok: bool
    seq: Optional[int] = None
    cert: Optional[str] = None
    detail: str = ""


@dataclass
class AuditReport:
    ok: bool
    n_events: int = 0
    n_certificates: int = 0
    steps: list[Step] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _quotes(av: Avayava, ds: list[Defeater]) -> list[tuple]:
    out = []
    if av.pratijna.paksa_mention:
        out.append(av.pratijna.paksa_mention)
    if av.upanaya:
        out.append(av.upanaya)
    for l in av.udaharana.loci:
        out.extend(l.facts)
    out.extend(d.quote for d in ds)
    return [(q.source_id, q.quote, q.located, q.start, q.end) for q in out]


def audit_certificate(body: dict[str, Any], texts_dir: Path, seq: Optional[int] = None) -> list[Step]:
    cid = body.get("id", "")
    steps: list[Step] = []

    def add(step: str, ok: bool, detail: str = "") -> None:
        steps.append(Step(step, ok, seq, cid, detail))

    add("certificate_id", cert_id(body) == cid, "" if cert_id(body) == cid else "id is not the hash of the body")

    texts: dict[str, str] = {}
    missing = []
    for sid, sha in body.get("texts", {}).items():
        f = Path(texts_dir) / f"{sha}.txt"
        if not f.exists():
            missing.append(f"{sid}: text {sha[:12]} not available")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            missing.append(f"{sid}: stored text does not match {sha[:12]}")
        else:
            texts[sid] = f.read_bytes().decode("utf-8")
    add("source_hashes", not missing, "; ".join(missing))

    try:
        av = Avayava.model_validate(body["avayava"])
        ds = [Defeater.model_validate(d) for d in body.get("defeaters", [])]
        src = Source.model_validate(body["source"])
    except Exception as e:  # a certificate that does not parse fails, it does not crash the audit
        add("schema", False, f"{type(e).__name__}: {e}")
        return steps

    claimed = _quotes(av, ds)
    av2, _ = ground(av, texts)
    ds2, _ = ground_defeaters(ds, texts)
    recomputed = _quotes(av2, ds2)
    bad = [f"{c[0]}:{c[1][:40]!r} claimed {c[2:]} recomputed {r[2:]}"
           for c, r in zip(claimed, recomputed) if c != r]
    add("quote_offsets", not bad and not missing,
        "; ".join(bad) or ("cannot re-locate without the source text" if missing else f"{len(claimed)} quotes"))

    world = build_world(av2, ds2, src)
    verdict, rule, subtype = derive_full(world)
    nig = av.nigamana
    got = (verdict.value, rule, subtype.value if subtype else None)
    want = (nig.verdict.value, nig.rule, nig.subtype.value if nig.subtype else None) if nig else None
    add("verdict", got == want, f"{got[0]} by {rule}" if got == want else f"certificate says {want}, derivation gives {got}")

    lam = body.get("checks", {}).get("pbs_lambda", 3.0)
    score = pbs(world, verdict, lam)
    same = nig is not None and set(score) == set(nig.pbs) and all(abs(score[k] - nig.pbs[k]) < 1e-12 for k in score)
    add("pbs", same, "" if same else f"certificate says {nig.pbs if nig else None}, recomputed {score}")
    return steps


def audit(path: Path, pubkey: Optional[str] = None, texts_dir: Optional[Path] = None) -> AuditReport:
    """Audit a ledger file. ``pubkey`` (base64) pins who must have signed the
    head; without it the signature is only checked for self-consistency."""
    path = Path(path)
    rep = AuditReport(ok=False)
    res = verify(path)
    rep.n_events = res.n
    rep.steps.append(Step("hash_chain", res.ok, res.first_bad_seq,
                          detail=f"{res.n} events, head {res.head_hash[:12]}" if res.ok else str(res.reason)))
    if not res.ok:
        return rep  # nothing after a broken link can be trusted

    sig = read_signature(path)
    if sig is None:
        rep.steps.append(Step("signature", False, detail="no signature on the chain head"))
    else:
        ok, detail = True, f"head seq {sig.get('seq')} signed by {str(sig.get('public_key'))[:16]}..."
        if sig.get("this_hash") != res.head_hash or sig.get("seq") != res.n - 1:
            ok, detail = False, f"signature covers seq {sig.get('seq')}, chain head is seq {res.n - 1}"
        elif pubkey is not None and sig.get("public_key") != pubkey:
            ok, detail = False, "signed by a different key than the one pinned"
        else:
            try:
                Ed25519PublicKey.from_public_bytes(base64.b64decode(sig["public_key"])).verify(
                    base64.b64decode(sig["signature"]), bytes.fromhex(sig["this_hash"]))
            except (InvalidSignature, ValueError, KeyError):
                ok, detail = False, "Ed25519 signature does not verify"
        if ok and pubkey is None:
            detail += " (key not pinned: self-consistent only)"
        rep.steps.append(Step("signature", ok, sig.get("seq"), detail=detail))

    tdir = texts_dir or sources_dir(path)
    for ev in iter_events(path):
        if ev.payload.get("kind") != PAYLOAD_KIND:
            continue
        rep.n_certificates += 1
        rep.steps.extend(audit_certificate(ev.payload["certificate"], tdir, ev.seq))
    rep.ok = all(s.ok for s in rep.steps)
    return rep
