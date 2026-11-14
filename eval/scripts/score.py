"""Metrics from predictions.jsonl. Written and frozen before the held-out run.

usage: score.py RUNDIR [--boot 10000]
"""
import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("--boot", type=int, default=10000)
a = ap.parse_args()
run = Path(a.run)
P = [json.loads(l) for l in open(run / "predictions.jsonl")]
C = [json.loads(l) for l in open(run / "calls.jsonl")]
SYSTEMS = ["direct_1", "direct_3", "taxonomy_1", "taxonomy_3", "pipeline_noguard", "pipeline", "pipeline_noground"]
SYSTEMS = [s for s in SYSTEMS if s in P[0]]
PRIMARY = "pipeline_noguard"
ABSTAIN = {"unresolved", "extraction_failed", "failed"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d), min(1.0, (c + h) / d))


def rate(k, n):
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else None, "wilson95": [round(lo, 4), round(hi, 4)]}


def metrics(rows, s):
    neg = [r for r in rows if r["label"] == "not_supported"]; pos = [r for r in rows if r["label"] == "supported"]
    fs = sum(r[s] == "supported" for r in neg); tp = sum(r[s] == "supported" for r in pos)
    ab = sum(r[s] in ABSTAIN for r in rows)
    return {"false_support_rate": rate(fs, len(neg)), "supported_recall": rate(tp, len(pos)),
            "precision_of_support": rate(tp, tp + fs), "abstention": rate(ab, len(rows)),
            "coverage": rate(len(rows) - ab, len(rows)),
            "confusion": {g: dict(Counter(r[s] for r in rows if r["label"] == g)) for g in ("supported", "not_supported")}}


def cluster_boot_diff(rows, s1, s2, key, seed=0):
    """Paired difference (s1 - s2) in a rate, resampling source families with
    replacement: items from one source are not independent."""
    fam = defaultdict(list)
    for r in rows:
        fam[r["family"]].append(r)
    fams = sorted(fam); rng = random.Random(seed); diffs = []
    def stat(rs):
        sel = [r for r in rs if r["label"] == key]
        if not sel:
            return None
        return (sum(r[s1] == "supported" for r in sel) - sum(r[s2] == "supported" for r in sel)) / len(sel)
    for _ in range(a.boot):
        d = stat([r for f in (rng.choice(fams) for _ in fams) for r in fam[f]])
        if d is not None:
            diffs.append(d)
    diffs.sort()
    return {"diff": stat(rows), "ci95": [diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]],
            "method": f"family-cluster bootstrap, {a.boot} resamples, seed {seed}"}


def mcnemar(rows, s1, s2):
    """Exact two-sided McNemar on item-level correctness. Assumes independent
    items, which related mutations of one source violate; read with the
    cluster bootstrap, not instead of it."""
    ok = lambda r, s: (r[s] == "supported") == (r["label"] == "supported")
    b = sum(ok(r, s1) and not ok(r, s2) for r in rows); c = sum(ok(r, s2) and not ok(r, s1) for r in rows)
    n = b + c
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n) if n else 1.0
    return {"only_first_correct": b, "only_second_correct": c, "p_exact": p}


out = {"n_items": len(P), "n_families": len({r["family"] for r in P}), "primary_system": PRIMARY, "systems": {}}
for s in SYSTEMS:
    m = metrics(P, s)
    m["by_slice"] = {sl: {k: v for k, v in metrics([r for r in P if r["slice"] == sl], s).items() if k != "confusion"}
                     for sl in sorted({r["slice"] for r in P})}
    m["false_support_by_subtype"] = {st: rate(sum(r[s] == "supported" for r in P if r["subtype"] == st),
                                              sum(1 for r in P if r["subtype"] == st))
                                     for st in sorted({r["subtype"] for r in P if r["subtype"]})}
    out["systems"][s] = m
out["paired"] = {}
for other in SYSTEMS:
    if other == PRIMARY or PRIMARY not in SYSTEMS:
        continue
    out["paired"][f"{PRIMARY} minus {other}"] = {
        "false_support": cluster_boot_diff(P, PRIMARY, other, "not_supported"),
        "supported_recall": cluster_boot_diff(P, PRIMARY, other, "supported"),
        "mcnemar_accuracy": mcnemar(P, PRIMARY, other)}

# pipeline internals
if "pipeline" in P[0]:
    q_prop = sum(r.get("quotes_proposed", 0) for r in P); q_loc = sum(r.get("quotes_located", 0) for r in P)
    runs = [s for r in P for s in r["pipeline_noguard_runs"]]
    out["pipeline"] = {
        "quote_location_rate": rate(q_loc, q_prop),
        "quote_refusal_reasons": dict(Counter(v for r in P for v in r.get("quote_reasons", {}).values())),
        "extraction_parse_failures": rate(sum(e is not None for r in P for e in r["extract_errors"]),
                                          sum(len(r["extract_errors"]) for r in P)),
        "items_all_runs_failed": sum(r[PRIMARY] == "extraction_failed" for r in P),
        "run_status_counts": dict(Counter(runs)),
        "stability_all_runs_agree": rate(sum(len(set(r["pipeline_noguard_runs"])) == 1 for r in P), len(P)),
        "reasons_on_unsupported_gold": dict(Counter(x for r in P if r["label"] == "not_supported"
                                                    for x in r.get("pipeline_reasons", []))),
        "reasons_on_supported_gold": dict(Counter(x for r in P if r["label"] == "supported"
                                                  for x in r.get("pipeline_reasons", []))),
    }
    # accuracy split by stability (stability is not confidence; this shows what it is worth)
    for name, sel in (("stable", lambda r: len(set(r["pipeline_noguard_runs"])) == 1),
                      ("unstable", lambda r: len(set(r["pipeline_noguard_runs"])) > 1)):
        rs = [r for r in P if sel(r)]
        out["pipeline"][f"accuracy_{name}"] = rate(
            sum((r[PRIMARY] == "supported") == (r["label"] == "supported") for r in rs), len(rs))
for kind in ("direct", "taxonomy"):
    if f"{kind}_runs" in P[0]:
        out.setdefault("baseline_stability", {})[kind] = rate(sum(len(set(r[f"{kind}_runs"])) == 1 for r in P), len(P))
        out.setdefault("baseline_parse_failures", {})[kind] = rate(
            sum(x == "failed" for r in P for x in r[f"{kind}_runs"]), sum(len(r[f"{kind}_runs"]) for r in P))

# cost
cost = {}
for sysname in sorted({c["tag"]["system"] for c in C}):
    cs = [c for c in C if c["tag"]["system"] == sysname]
    ok = [c for c in cs if c.get("ok")]
    cost[sysname] = {"calls": len(cs), "failed_calls": len(cs) - len(ok), "retried_calls": sum(c["attempts"] > 1 for c in cs),
                     "mean_latency_s": round(sum(c["latency_s"] for c in ok) / len(ok), 2),
                     "mean_input_tokens": round(sum(c["input_tokens"] for c in ok) / len(ok)),
                     "mean_output_tokens": round(sum(c["output_tokens"] for c in ok) / len(ok)),
                     "total_cost_usd": round(sum(c.get("cost_usd") or 0 for c in ok), 4),
                     "cost_per_call_usd": round(sum(c.get("cost_usd") or 0 for c in ok) / len(ok), 5)}
out["cost_per_call_by_prompt"] = cost
out["calls_per_item"] = {"direct_1": 1, "taxonomy_1": 1, "direct_3": 3, "taxonomy_3": 3, "pipeline*": 3}
(run / "metrics.json").write_text(json.dumps(out, indent=1))
print(f"{'system':20s} {'false-support':>22s} {'recall':>22s} {'precision':>10s} {'abstain':>8s}")
for s in SYSTEMS:
    m = out["systems"][s]; f = m["false_support_rate"]; r = m["supported_recall"]; pr = m["precision_of_support"]
    print(f"{s:20s} {f['k']:3d}/{f['n']:<3d} {str(f['wilson95']):>15s} {r['k']:3d}/{r['n']:<3d} {str(r['wilson95']):>15s} "
          f"{(pr['rate'] or 0):10.3f} {m['abstention']['k']:8d}")
