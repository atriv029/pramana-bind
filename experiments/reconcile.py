"""One authoritative metrics source: submission/metrics_master.json. Everything is recomputed from raw artifacts.
Also writes the item -> record -> certificate coverage manifest and the paired qualifier transitions."""
import glob, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path
from pramana_bind import v3
from pravrudhi_kernel.ledger.verify import iter_events

R = Path(__file__).resolve().parents[1]
DS = ["contractnli", "vitaminc", "scicite", "attributionbench"]
M = {"calls": {}, "quotes": {}, "certificates": {}, "qualifier": {}}

def calls(path):
    ok = set(); recs = 0; failed = 0; cost = 0.0; by = Counter(); served = Counter(); errs = Counter()
    for l in open(path):
        c = json.loads(l); recs += 1
        if c.get("ok"):
            k = (c["tag"]["system"], c["tag"]["item"], c["tag"]["run"])
            if k not in ok:
                ok.add(k); cost += c.get("cost_usd") or 0; by[c["tag"]["system"] + ("" if c["tag"]["run"] == 0 else "_repeat")] += 1; served[c.get("served_model")] += 1
        else:
            failed += 1; errs[(c.get("error") or "")[:40]] += 1
    return {"successful_calls": len(ok), "failed_call_records": failed, "cost_usd": round(cost, 2), "by_prompt": dict(by),
            "served_models": dict(served), "failure_reasons": dict(errs)}

SCOPES = {
 "exp1_development (21 items; prompt v2 then v3; baselines copied into the v3 folder are counted once, in v2)": ["eval/runs/dev-haiku-promptv2/calls.jsonl"],
 "exp1_development_extract_v3": ["eval/runs/dev-haiku-promptv3/calls.jsonl"],
 "exp1_attack_development (7 items)": ["eval/runs/attackdev-haiku/calls.jsonl"],
 "exp1_heldout (117 items)": ["eval/runs/test-haiku/calls.jsonl"],
 "exp1_attack_heldout (23 items)": ["eval/runs/attacktest-haiku/calls.jsonl"],
 "exp2_development (dev1, dev2, dev3)": sorted(glob.glob(str(R / "experiments/exp2/runs/dev*/calls.jsonl"))),
 "exp2_heldout_main (754 items x 4 prompts, run 0)": None, "exp2_heldout_repeats (40 items x 4 datasets x 2 prompts x 2 extra runs)": None,
 "exp3_second_model": sorted(glob.glob(str(R / "experiments/exp3/runs/*/calls.jsonl"))),
}
for name, paths in SCOPES.items():
    if paths is None:
        continue
    agg = {"successful_calls": 0, "failed_call_records": 0, "cost_usd": 0.0, "by_prompt": Counter(), "served_models": Counter(), "failure_reasons": Counter()}
    for p in paths:
        c = calls(R / p if not str(p).startswith("/") else p)
        for k in ("successful_calls", "failed_call_records", "cost_usd"):
            agg[k] += c[k]
        for k in ("by_prompt", "served_models", "failure_reasons"):
            agg[k].update(c[k])
    if name == "exp1_development_extract_v3":   # the v3 folder contains copies of the v2 baseline calls; count only its extract calls
        ex = sum(1 for l in open(R / paths[0]) if json.loads(l).get("ok") and json.loads(l)["tag"]["system"] == "extract")
        agg = {"successful_calls": ex, "failed_call_records": 0, "cost_usd": round(sum((json.loads(l).get("cost_usd") or 0) for l in open(R / paths[0]) if json.loads(l)["tag"]["system"] == "extract"), 2), "by_prompt": {"extract": ex}, "served_models": {}, "failure_reasons": {}}
    agg["cost_usd"] = round(agg["cost_usd"], 2)
    M["calls"][name] = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in agg.items()}
main = {"successful_calls": 0, "cost_usd": 0.0, "failed_call_records": 0}; rep = {"successful_calls": 0, "cost_usd": 0.0}
for d in DS:
    seen = set()
    for l in open(R / f"experiments/exp2/runs/eval-{d}/calls.jsonl"):
        c = json.loads(l)
        if not c.get("ok"):
            main["failed_call_records"] += 1; continue
        k = (c["tag"]["system"], c["tag"]["item"], c["tag"]["run"])
        if k in seen:
            continue
        seen.add(k); tgt = main if c["tag"]["run"] == 0 else rep
        tgt["successful_calls"] += 1; tgt["cost_usd"] += c.get("cost_usd") or 0
main["cost_usd"] = round(main["cost_usd"], 2); rep["cost_usd"] = round(rep["cost_usd"], 2)
M["calls"]["exp2_heldout_main (754 items x 4 prompts, run 0)"] = main
M["calls"]["exp2_heldout_repeats (40 items x 4 datasets x 2 prompts x 2 extra runs)"] = rep
ev = main["successful_calls"] + rep["successful_calls"]; dv = M["calls"]["exp2_development (dev1, dev2, dev3)"]["successful_calls"]
M["calls"]["RECONCILIATION"] = {
    "exp2_heldout_total": ev, "exp2_heldout_cost": round(main["cost_usd"] + rep["cost_usd"], 2),
    "exp2_development_total": dv, "exp2_all": ev + dv,
    "exp2_all_cost": round(main["cost_usd"] + rep["cost_usd"] + M["calls"]["exp2_development (dev1, dev2, dev3)"]["cost_usd"], 2),
    "explanation": "The earlier report's figure counted held-out evaluation calls only; the earlier status message's figure added the development pilots."}

# quotes, per system and dataset, run 0, from the raw replies (independent of rule version)
cov = []
for d in DS:
    items = [json.loads(l) for l in open(R / f"experiments/exp2/data/{d}_eval.jsonl")]
    raw = {}
    for l in open(R / f"experiments/exp2/runs/eval-{d}/calls.jsonl"):
        c = json.loads(l)
        if c.get("ok") and c["tag"]["run"] == 0:
            raw[(c["tag"]["system"], c["tag"]["item"])] = c["text"]
    old = {e.payload["certificate"]["subject"]["item_id"]: e.payload["certificate"]["id"] for e in iter_events(R / "experiments/exp2/ledger/ledger.jsonl") if e.payload.get("kind") == "pramana_certificate"}
    new = {e.payload["certificate"]["subject"]["item_id"]: (e.payload["certificate"]["id"], e.seq) for e in iter_events(R / "experiments/exp2b/ledger/ledger.jsonl") if e.payload.get("kind") == "pramana_certificate"}
    q = {s: {"proposed": 0, "located": 0, "refusal_reasons": Counter(), "items_with_a_refused_quote": 0, "items_whose_status_changes_without_grounding": 0} for s in ("N1", "B1")}
    for it in items:
        text = it["sources"][0]["text"]
        for s in ("N1", "B1"):
            rec = v3.parse_record(raw.get((s, it["id"]), ""))
            if rec is None:
                if s == "N1":
                    cov.append({"item": it["id"], "dataset": d, "n1_reply": "present" if (s, it["id"]) in raw else "missing", "n1_record": "malformed (not parseable JSON object)",
                                "certificate_rules_3.1": None, "certificate_rules_3.2": None, "scored_as": "failed (kept in every denominator)"})
                continue
            dd = (v3.decide_n1 if s == "N1" else v3.decide_b1)(rec, text); ng = (v3.decide_n1 if s == "N1" else v3.decide_b1)(rec, text, grounding=False)
            locs = dd["evidence_located"] + dd.get("qualifiers_located", [])
            q[s]["proposed"] += dd["quotes_proposed"]; q[s]["located"] += dd["quotes_located"]
            bad = [l["reason"] for l in locs if not l["located"]]
            # B1 missing_conditions quotes are inside quotes_proposed but not in evidence_located; count refusals by difference
            q[s]["refusal_reasons"].update(bad); q[s]["items_with_a_refused_quote"] += dd["quotes_located"] < dd["quotes_proposed"]
            q[s]["items_whose_status_changes_without_grounding"] += dd["status"] != ng["status"]
            if s == "N1":
                cov.append({"item": it["id"], "dataset": d, "n1_reply": "present", "n1_record": "parsed", "certificate_rules_3.1": old.get(it["id"]),
                            "certificate_rules_3.2": new.get(it["id"], (None,))[0], "ledger_seq_3.2": new.get(it["id"], (None, None))[1],
                            "parts": len(dd["parts"]), "part_numbering": dd["part_numbering"], "invalid_part_references": dd["invalid_part_references"], "scored_as": dd["status"]})
    M["quotes"][d] = {s: {**v, "refusal_reasons": dict(v["refusal_reasons"])} for s, v in q.items()}
for s in ("N1", "B1"):
    M["quotes"][f"TOTAL_{s}"] = {k: sum(M["quotes"][d][s][k] for d in DS) for k in ("proposed", "located", "items_with_a_refused_quote", "items_whose_status_changes_without_grounding")}
M["quotes"]["TOTAL_N1_plus_B1"] = {k: M["quotes"]["TOTAL_N1"][k] + M["quotes"]["TOTAL_B1"][k] for k in ("proposed", "located")}
M["quotes"]["exp1"] = json.load(open(R / "eval/runs/test-haiku/metrics.json"))["pipeline"]["quote_location_rate"]
(R / "submission/COVERAGE_MANIFEST.json").write_text(json.dumps(cov, indent=0))
M["certificates"] = {"exp2_items": len(cov), "n1_records_parsed": sum(c["n1_record"] == "parsed" for c in cov),
                     "certificates_rules_3.1": sum(bool(c["certificate_rules_3.1"]) for c in cov), "certificates_rules_3.2": sum(bool(c["certificate_rules_3.2"]) for c in cov),
                     "items_without_certificate": [c["item"] for c in cov if not c["certificate_rules_3.2"]],
                     "many_to_one": "none: certificate ids are content hashes that include the item id, so each certificate maps to exactly one item",
                     "explanation": "754 items, 753 certificates: one N1 reply (SciCiteVal) was not a parseable JSON object. It has no certificate, is scored as a failure and stays in every denominator. No de-duplication occurs.",
                     "part_numbering": dict(Counter(c.get("part_numbering") for c in cov if c["n1_record"] == "parsed")),
                     "multi_part_records": sum(c.get("parts", 0) > 1 for c in cov), "records_with_invalid_part_reference": sum(c.get("invalid_part_references", 0) > 0 for c in cov),
                     "exp1_certificates": 117}

# paired qualifier transitions (rules N1/3.2), every change of status, with full context
trans_all = []
for d in DS:
    items = {json.loads(l)["id"]: json.loads(l) for l in open(R / f"experiments/exp2/data/{d}_eval.jsonl")}
    P = [json.loads(l) for l in open(R / f"experiments/exp2b/runs/eval-{d}/predictions.jsonl")]
    raw = {json.loads(l)["tag"]["item"]: json.loads(l)["text"] for l in open(R / f"experiments/exp2/runs/eval-{d}/calls.jsonl")
           if json.loads(l).get("ok") and json.loads(l)["tag"]["system"] == "N1" and json.loads(l)["tag"]["run"] == 0}
    t = Counter()
    for p in P:
        g = "supported" if p["gold"] == "supported" else "unsupported"
        t[(g, p["N1"], p["N1_noqual"])] += 1
        if p["N1"] != p["N1_noqual"]:
            it = items[p["id"]]; rec = v3.parse_record(raw[p["id"]]); on = v3.decide_n1(rec, it["sources"][0]["text"])
            blockers = []
            for qq, loc, qi in zip(rec.get("qualifiers") or [], on["qualifiers_located"], on["qualifier_part_index"]):
                part = ((rec.get("claim") or {}).get("parts") or [{}])[qi] if qi is not None and qi < len((rec.get("claim") or {}).get("parts") or [{}]) else {}
                blocks = bool(loc["located"] and qq.get("stated_in_claim") is not True and qi is not None and (
                    (qq.get("relation") in v3.BLOCKING and qq.get("claim_part_changed") != "none") or (qq.get("relation") == "exception" and part.get("universal_wording") is True)))
                blockers.append({"relation": qq.get("relation"), "claim_part_changed": qq.get("claim_part_changed"), "stated_in_claim": qq.get("stated_in_claim"),
                                 "text": qq.get("text"), "quote": qq.get("quote"), "located": loc["located"], "start": loc.get("start"), "end": loc.get("end"),
                                 "part_index": qi, "blocks_under_rule": blocks})
            trans_all.append({"dataset": d, "item": p["id"], "family": p["family"], "claim": it["claim"], "source_sha256": it["sources"][0]["sha256"],
                              "source_text": it["sources"][0]["text"] if len(it["sources"][0]["text"]) < 6000 else None,
                              "source_ref_if_long": f"experiments/exp2/data/{d}_eval.jsonl" if len(it["sources"][0]["text"]) >= 6000 else None,
                              "reference_label": it["original_label"], "gold": p["gold"], "with_enforcement": p["N1"], "without_enforcement": p["N1_noqual"],
                              "reasons_with_enforcement": on["reasons"], "extraction": rec, "qualifiers": blockers, "human_judgment": None})
    M["qualifier"][d] = {"transitions (gold, with, without)": {" | ".join(k): v for k, v in sorted(t.items())},
                         "supported_gold_newly_accepted": sum(v for (g, a, b), v in t.items() if g == "supported" and a != "supported" and b == "supported"),
                         "unsupported_gold_newly_accepted": sum(v for (g, a, b), v in t.items() if g == "unsupported" and a != "supported" and b == "supported"),
                         "acceptances_lost": sum(v for (g, a, b), v in t.items() if a == "supported" and b != "supported"),
                         "changes_among_non_support": sum(v for (g, a, b), v in t.items() if a != b and "supported" not in (a, b)),
                         "items_changed": sum(v for (g, a, b), v in t.items() if a != b)}
M["qualifier"]["TOTAL"] = {k: sum(M["qualifier"][d][k] for d in DS) for k in ("supported_gold_newly_accepted", "unsupported_gold_newly_accepted", "acceptances_lost", "changes_among_non_support", "items_changed")}
M["qualifier"]["monotonic"] = M["qualifier"]["TOTAL"]["acceptances_lost"] == 0 and M["qualifier"]["TOTAL"]["changes_among_non_support"] == 0
(R / "submission/QUALIFIER_TRANSITIONS.json").write_text(json.dumps(trans_all, indent=0, ensure_ascii=False))
(R / "submission/metrics_master.json").write_text(json.dumps(M, indent=1))
print(json.dumps(M["calls"]["RECONCILIATION"])); print({k: (v["successful_calls"], v["failed_call_records"] if "failed_call_records" in v else "", v["cost_usd"]) for k, v in M["calls"].items() if k != "RECONCILIATION"})
print({k: v for k, v in M["quotes"].items() if k.startswith("TOTAL") or k == "exp1"}); print({d: M["quotes"][d]["N1"]["refusal_reasons"] for d in DS})
print({k: v for k, v in M["certificates"].items() if k not in ("explanation", "many_to_one")}); print(M["qualifier"]["TOTAL"], M["qualifier"]["monotonic"]); print({d: M["qualifier"][d] for d in DS})
