"""Experiment 2 runner. Resumable; every call (failed ones too) is appended raw to calls.jsonl.
Caching: a successful (system, item, run) call is never re-issued. Retries: transport/CLI errors only, 2 retries
inside a call, and failed calls are re-issued on the next invocation. Malformed answers are kept and counted.

usage: run.py ITEMS.jsonl OUTDIR --model M [--systems B0,T,B1,N1] [--extra-subset 40] [--workers 8]
"""
import argparse, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pramana_bind import v3
from pramana_bind.models import ClaudeCLI

ap = argparse.ArgumentParser()
ap.add_argument("items"); ap.add_argument("out"); ap.add_argument("--model", required=True)
ap.add_argument("--systems", default="B0,T,B1,N1"); ap.add_argument("--extra-subset", type=int, default=0)
ap.add_argument("--workers", type=int, default=8); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
items = [json.loads(l) for l in open(a.items)]
if a.limit:
    items = items[:a.limit]
model = ClaudeCLI(a.model, out / "calls.jsonl", timeout=240)
systems = a.systems.split(",")
done = {}
if (out / "calls.jsonl").exists():
    for l in open(out / "calls.jsonl"):
        r = json.loads(l)
        if r.get("ok"):
            done[(r["tag"]["system"], r["tag"]["item"], r["tag"]["run"])] = r
# opaque ids in tags only; prompts contain claim and source text and nothing else from the item
jobs = []
for n, it in enumerate(items):
    for s in systems:
        runs = [0] + ([1, 2] if (n < a.extra_subset and s in ("B0", "N1")) else [])
        for run in runs:
            if (s, it["id"], run) not in done:
                jobs.append((v3.render(s, it["claim"], it["sources"][0]["text"], it["dataset"]), {"system": s, "item": it["id"], "run": run}))
print(f"{len(jobs)} calls to make, {len(done)} cached", flush=True)
with ThreadPoolExecutor(a.workers) as ex:
    for r in ex.map(lambda j: model.call(*j), jobs):
        if r.get("ok"):
            done[(r["tag"]["system"], r["tag"]["item"], r["tag"]["run"])] = r
(out / "config.json").write_text(json.dumps({"model": model.config(), "items_file": a.items, "n_items": len(items),
    "systems": systems, "extra_subset": a.extra_subset, "prompt_sha256": v3.PROMPT_SHA256,
    "rules": {"N1": v3.RULES_VERSION, "B1": v3.B1_RULES_VERSION}, "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=1))


def maj(labels):
    labels = [l for l in labels if l]
    if not labels:
        return "failed"
    for lab in ("supported", "contradicted"):
        if labels.count(lab) * 2 > len(labels):
            return lab
    return "not_established"


preds = []
for n, it in enumerate(items):
    text = it["sources"][0]["text"]
    row = {"id": it["id"], "dataset": it["dataset"], "family": it["source_family_id"], "gold": it["support_gold"],
           "original_label": it["original_label"], "tags_gold": it.get("failure_tags_gold", []),
           "src_dataset": it.get("src_dataset"), "in_extra_subset": n < a.extra_subset}
    get = lambda s, run=0: done.get((s, it["id"], run))
    for s in ("B0", "T"):
        if s in systems:
            c = get(s); row[s] = (v3.parse_label(c["text"]) if c else None) or "failed"
            if s == "T" and c:
                row["T_category"] = (v3.parse_record(c["text"]) or {}).get("category")
    if "B1" in systems:
        rec = v3.parse_record(get("B1")["text"]) if get("B1") else None
        if rec is None:
            row["B1"] = "failed"
        else:
            d = v3.decide_b1(rec, text); row.update(B1=d["status"], B1_reasons=d["reasons"],
                                                   B1_quotes=[d["quotes_located"], d["quotes_proposed"]])
    if "N1" in systems:
        rec = v3.parse_record(get("N1")["text"]) if get("N1") else None
        if rec is None:
            row["N1"] = row["N1_noqual"] = row["N1_noground"] = "failed"
        else:
            d = v3.decide_n1(rec, text)
            row.update(N1=d["status"], N1_reasons=d["reasons"], N1_path=d["path"], N1_conflict=d["conflict"],
                       N1_quotes=[d["quotes_located"], d["quotes_proposed"]],
                       N1_noqual=v3.decide_n1(rec, text, use_qualifiers=False)["status"],     # rule-only ablations of
                       N1_noground=v3.decide_n1(rec, text, grounding=False)["status"])        # the SAME extraction
    if n < a.extra_subset:
        if "B0" in systems:
            ls = [v3.parse_label(get("B0", r)["text"]) if get("B0", r) else None for r in range(3)]
            row["B0_runs"] = [l or "failed" for l in ls]; row["B0x3"] = maj(ls)
        if "N1" in systems:
            ls = []
            for r in range(3):
                rec = v3.parse_record(get("N1", r)["text"]) if get("N1", r) else None
                ls.append(v3.decide_n1(rec, text)["status"] if rec else None)
            row["N1_runs"] = [l or "failed" for l in ls]; row["N1x3"] = maj(ls)
    preds.append(row)
(out / "predictions.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in preds))
print("predictions:", len(preds))
