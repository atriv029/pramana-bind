"""Experiment 2 metrics. usage: score.py RUNDIR [--boot 5000]"""
import argparse, json, math, random
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("--boot", type=int, default=5000)
a = ap.parse_args(); run = Path(a.run)
P = [json.loads(l) for l in open(run / "predictions.jsonl")]
C = [json.loads(l) for l in open(run / "calls.jsonl")]
SYS = [s for s in ("B0", "T", "B1", "N1", "N1_noqual", "N1_noground") if s in P[0]]
three_way = any(p["gold"] == "contradicted" for p in P)
sup = lambda x: x == "supported"


def wilson(k, n, z=1.96):
    if not n:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(max(0, (c - h) / d), 4), round(min(1, (c + h) / d), 4)]


def rate(k, n):
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None, "wilson95": wilson(k, n)}


def macro_f1(rows, s):
    f = []
    for lab in ("supported", "contradicted", "not_established"):
        tp = sum(r[s] == lab and r["gold"] == lab for r in rows); fp = sum(r[s] == lab and r["gold"] != lab for r in rows)
        fn = sum(r[s] != lab and r["gold"] == lab for r in rows)
        f.append(2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0)
    return round(sum(f) / 3, 4)


def metrics(rows, s):
    neg = [r for r in rows if not sup(r["gold"])]; pos = [r for r in rows if sup(r["gold"])]
    fs = sum(sup(r[s]) for r in neg); tp = sum(sup(r[s]) for r in pos)
    m = {"false_support": rate(fs, len(neg)), "supported_recall": rate(tp, len(pos)), "support_precision": rate(tp, tp + fs),
         "failed": rate(sum(r[s] == "failed" for r in rows), len(rows)),
         "confusion": {g: dict(Counter(r[s] for r in rows if r["gold"] == g)) for g in sorted({r["gold"] for r in rows})}}
    if three_way:
        m["accuracy_3way"] = rate(sum(r[s] == r["gold"] for r in rows), len(rows)); m["macro_f1_3way"] = macro_f1(rows, s)
    return m


def boot(rows, fn, seed=0):
    fam = defaultdict(list)
    for r in rows:
        fam[r["family"]].append(r)
    fams = sorted(fam); rng = random.Random(seed); vals = []
    for _ in range(a.boot):
        v = fn([r for f in (rng.choice(fams) for _ in fams) for r in fam[f]])
        if v is not None:
            vals.append(v)
    vals.sort()
    return {"diff": round(fn(rows), 4) if fn(rows) is not None else None,
            "ci95": [round(vals[int(.025 * len(vals))], 4), round(vals[int(.975 * len(vals)) - 1], 4)] if vals else None}


def diff_fn(s1, s2, kind):
    def f(rows):
        if kind == "acc":
            return sum((r[s1] == r["gold"]) - (r[s2] == r["gold"]) for r in rows) / len(rows) if rows else None
        sel = [r for r in rows if sup(r["gold"]) == (kind == "recall")]
        return sum(sup(r[s1]) - sup(r[s2]) for r in sel) / len(sel) if sel else None
    return f


out = {"n": len(P), "families": len({p["family"] for p in P}), "three_way_gold": three_way,
       "gold": dict(Counter(p["gold"] for p in P)), "systems": {s: metrics(P, s) for s in SYS}, "paired_vs_N1": {}}
for s in SYS:
    if s != "N1" and "N1" in SYS:
        out["paired_vs_N1"][f"N1 minus {s}"] = {
            "false_support": boot(P, diff_fn("N1", s, "fs")), "supported_recall": boot(P, diff_fn("N1", s, "recall")),
            **({"accuracy_3way": boot(P, diff_fn("N1", s, "acc"))} if three_way else {}),
            "method": f"family-cluster bootstrap, {a.boot} resamples, seed 0; {len(SYS) - 1} comparisons, unadjusted"}
# slices
for key in ("original_label", "src_dataset"):
    vals = sorted({str(p.get(key)) for p in P if p.get(key)})
    if 1 < len(vals) <= 8:
        out[f"by_{key}"] = {v: {s: rate(sum(sup(p[s]) for p in P if str(p.get(key)) == v), sum(1 for p in P if str(p.get(key)) == v))
                                for s in SYS} for v in vals}
        out[f"by_{key}_note"] = "cell = share predicted 'supported' within that gold stratum"
tags = sorted({t for p in P for t in p.get("tags_gold", [])})
if tags:
    out["accepted_by_distortion_tag"] = {t: {s: rate(sum(sup(p[s]) for p in P if t in p["tags_gold"]),
                                                     sum(1 for p in P if t in p["tags_gold"])) for s in SYS} for t in tags}
# contrast groups (families with >1 gold label): all rows of the group correct
groups = defaultdict(list)
for p in P:
    groups[p["family"]].append(p)
cg = [g for g in groups.values() if len({r["gold"] for r in g}) > 1]
if cg and len(cg) > 5:
    out["contrast_groups"] = {"n_groups": len(cg), "joint_correct": {
        s: rate(sum(all((r[s] == r["gold"]) if three_way else (sup(r[s]) == sup(r["gold"])) for r in g) for g in cg), len(cg)) for s in SYS}}
# structure internals
for s in ("B1", "N1"):
    k = [p.get(f"{s}_quotes") for p in P if p.get(f"{s}_quotes")]
    if k:
        out[f"{s}_quote_location"] = rate(sum(x[0] for x in k), sum(x[1] for x in k))
if "N1" in SYS:
    out["N1_reasons_by_gold"] = {g: dict(Counter(x.split(":")[-1] for p in P if p["gold"] == g for x in p.get("N1_reasons", [])))
                                 for g in sorted({p["gold"] for p in P})}
    out["N1_path"] = dict(Counter(p.get("N1_path") for p in P)); out["N1_conflict_flagged"] = sum(bool(p.get("N1_conflict")) for p in P)
sub = [p for p in P if p.get("in_extra_subset") and "N1x3" in p]
if sub:
    out["stability_subset"] = {"n": len(sub), "N1_runs_agree": rate(sum(len(set(p["N1_runs"])) == 1 for p in sub), len(sub)),
                               "B0_runs_agree": rate(sum(len(set(p["B0_runs"])) == 1 for p in sub), len(sub)),
                               "systems": {s: {k: v for k, v in metrics(sub, s).items() if k != "confusion"}
                                           for s in ("B0", "B0x3", "N1", "N1x3")}}
cost = {}
for s in sorted({c["tag"]["system"] for c in C}):
    ok = [c for c in C if c["tag"]["system"] == s and c.get("ok")]; bad = [c for c in C if c["tag"]["system"] == s and not c.get("ok")]
    if ok:
        cost[s] = {"ok_calls": len(ok), "failed_call_records": len(bad), "mean_latency_s": round(sum(c["latency_s"] for c in ok) / len(ok), 2),
                   "mean_input_tokens": round(sum(c["input_tokens"] for c in ok) / len(ok)), "mean_output_tokens": round(sum(c["output_tokens"] for c in ok) / len(ok)),
                   "cost_per_call_usd": round(sum(c.get("cost_usd") or 0 for c in ok) / len(ok), 5),
                   "total_cost_usd": round(sum(c.get("cost_usd") or 0 for c in ok), 3),
                   "served_models": dict(Counter(c.get("served_model") for c in ok))}
out["cost"] = cost
(run / "metrics.json").write_text(json.dumps(out, indent=1))
hdr = f"{'system':12s} {'false-support':>14s} {'recall':>12s}" + (f" {'acc3':>6s} {'F1-3':>6s}" if three_way else "") + " failed"
print(run.name, "| n", len(P), "| gold", out["gold"]); print(hdr)
for s in SYS:
    m = out["systems"][s]
    print(f"{s:12s} {m['false_support']['k']:5d}/{m['false_support']['n']:<5d}    {m['supported_recall']['k']:4d}/{m['supported_recall']['n']:<4d}"
          + (f"   {m['accuracy_3way']['rate']:.3f}  {m['macro_f1_3way']:.3f}" if three_way else "") + f"   {m['failed']['k']}")
