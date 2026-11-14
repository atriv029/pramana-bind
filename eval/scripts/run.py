"""Run every system on an item file. Resumable: each model call is cached by
(system, item, run). Raw responses are kept, malformed ones included.

usage: run.py ITEMS.jsonl OUTDIR --model claude-haiku-5-5 [--runs 3] [--workers 8]
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pramana_bind import baselines, certificate as cert
from pramana_bind.bind import ExtractionError, bind_extractions
from pramana_bind.extract import PROMPT_SHA256, Extraction, parse, render_prompt
from pramana_bind.models import ClaudeCLI

ap = argparse.ArgumentParser()
ap.add_argument("items"); ap.add_argument("out"); ap.add_argument("--model", required=True)
ap.add_argument("--runs", type=int, default=3); ap.add_argument("--workers", type=int, default=8)
ap.add_argument("--systems", default="extract,direct,taxonomy")
a = ap.parse_args()

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
items = [json.loads(l) for l in open(a.items)]
model = ClaudeCLI(a.model, out / "calls.jsonl")
(out / "config.json").write_text(json.dumps({
    "model": model.config(), "runs": a.runs, "items_file": a.items, "n_items": len(items),
    "prompt_sha256": {"extract": PROMPT_SHA256, **baselines.PROMPT_SHA256},
    "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}, indent=1))

done = {}
if (out / "calls.jsonl").exists():
    for l in open(out / "calls.jsonl"):
        r = json.loads(l)
        if r.get("ok"):
            done[(r["tag"]["system"], r["tag"]["item"], r["tag"]["run"])] = r

jobs = []
for it in items:
    for system in a.systems.split(","):
        for run in range(a.runs):
            if (system, it["id"], run) in done:
                continue
            prompt = (render_prompt(it["claim"], it["source_text"], it["citation"]) if system == "extract"
                      else baselines.render(system, it["claim"], it["source_text"], it["citation"]))
            jobs.append((prompt, {"system": system, "item": it["id"], "run": run}))
print(f"{len(jobs)} calls to make, {len(done)} cached", flush=True)
with ThreadPoolExecutor(a.workers) as ex:
    for r in ex.map(lambda j: model.call(*j), jobs):
        if r.get("ok"):
            done[(r["tag"]["system"], r["tag"]["item"], r["tag"]["run"])] = r

# ---- derive predictions from the raw calls (no model call below this line)
ledger_path = out / "ledger.jsonl"
if ledger_path.exists():
    ledger_path.unlink()
ledger = cert.open_ledger(ledger_path)
preds = []
for it in items:
    row = {"id": it["id"], "family": it["family"], "slice": it["slice"], "label": it["label"], "subtype": it["subtype"]}
    calls = {s: [done.get((s, it["id"], r)) for r in range(a.runs)] for s in a.systems.split(",")}
    # baselines
    for kind in ("direct", "taxonomy"):
        if kind not in calls:
            continue
        parsed = [baselines.parse_label(kind, c["text"]) if c else (None, None) for c in calls[kind]]
        labels = [p[0] for p in parsed]
        row[f"{kind}_1"] = labels[0] or "failed"
        row[f"{kind}_3"] = baselines.majority(labels)
        row[f"{kind}_runs"] = [l or "failed" for l in labels]
        if kind == "taxonomy":
            row["taxonomy_categories"] = [p[1] for p in parsed]
    # pipeline and its ablations, all from the SAME three extraction replies
    if "extract" in calls:
        exs = []
        for c in calls["extract"]:
            if not c:
                exs.append(Extraction(None, "", "call failed")); continue
            try:
                exs.append(Extraction(parse(c["text"]), c["text"]))
            except Exception as e:  # noqa: BLE001 - malformed replies are kept and counted
                exs.append(Extraction(None, c["text"], f"{type(e).__name__}: {e}"))
        row["extract_errors"] = [e.error for e in exs]
        for name, kw in (("pipeline", {}), ("pipeline_noguard", {"guard": False}),
                         ("pipeline_noground", {"grounding": False, "guard": False})):
            try:
                body, texts = bind_extractions(it["claim"], it["source_text"], exs, citation_raw=it["citation"],
                                               model=a.model, **kw)
                row[name] = body["status"]
                row[f"{name}_runs"] = body["extraction"]["run_statuses"]
                if name == "pipeline":
                    n = body["avayava"]["nigamana"]
                    row.update(pipeline_reasons=n["reasons"], pipeline_verdict=n["verdict"], pipeline_rule=n["rule"],
                               pipeline_pbs=n["pbs"]["value"], pipeline_unstable=body["extraction"]["unstable"],
                               cert_id=body["id"],
                               quotes_proposed=len(body["ground_reasons"]),
                               quotes_located=sum(v == "ok" for v in body["ground_reasons"].values()),
                               quote_reasons=body["ground_reasons"])
                    body["subject"]["item_id"] = it["id"]
                    body["id"] = cert.cert_id(body); row["cert_id"] = body["id"]
                    cert.emit(body, ledger, texts)
            except ExtractionError:
                row[name] = "extraction_failed"; row[f"{name}_runs"] = ["extraction_failed"] * a.runs
    preds.append(row)
(out / "predictions.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in preds))
key = out / "signer.key"
if not key.exists():
    (out / "signer.pub").write_text(cert.generate_key(key) + "\n")
cert.sign_head(ledger_path, cert.load_key(key))
rep = cert.audit(ledger_path, (out / "signer.pub").read_text().strip())
print("predictions:", len(preds), "| ledger audit ok:", rep.ok, "| certificates:", rep.n_certificates)
