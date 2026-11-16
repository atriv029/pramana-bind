"""Import and analyse the single-author review of the 30-item subset. No model call.
Inputs: the archived upload (never modified), the private key (not distributed), Experiment 1 predictions."""
import csv, hashlib, json, math, random
from collections import Counter, defaultdict
from pathlib import Path

H = Path(__file__).parent; R = H.parents[1]
raw_path = H / "reviewer_R1_original_upload.csv"
key = json.load(open(R / "review_admin_v2/KEY_DO_NOT_SHARE.json"))
expected = {r for r, v in key.items() if v["in_priority_30"]}
rows = list(csv.DictReader(open(raw_path, newline="", encoding="utf-8")))
LAB = [c for c in rows[0] if c.startswith("label")][0]; REASON = [c for c in rows[0] if c.startswith("reason")][0]
log, clean = [], []
ids = [r["review_id"].strip() for r in rows]
VALID = {"supported", "contradicted", "not_established", "ambiguous"}
for n, r in enumerate(rows, 2):
    c = dict(review_id=r["review_id"].strip(), label=r[LAB].strip(), reason=r[REASON],
             reviewer=r["reviewer_pseudonym"].strip(), timestamp=r["timestamp_utc"].strip())
    for f, a, b in (("review_id", r["review_id"], c["review_id"]), ("label", r[LAB], c["label"]),
                    ("reviewer_pseudonym", r["reviewer_pseudonym"], c["reviewer"]), ("timestamp_utc", r["timestamp_utc"], c["timestamp"])):
        if a != b:
            log.append({"line": n, "review_id": c["review_id"], "field": f, "from": a, "to": b, "kind": "whitespace trimmed"})
    clean.append(c)
val = {"sha256_of_upload": hashlib.sha256(raw_path.read_bytes()).hexdigest(), "rows": len(rows),
       "expected_ids": len(expected), "missing_ids": sorted(expected - set(ids)), "unexpected_ids": sorted(set(ids) - expected),
       "duplicate_ids": sorted(k for k, v in Counter(ids).items() if v > 1),
       "invalid_labels": [c["review_id"] for c in clean if c["label"] not in VALID],
       "empty_reasons": [c["review_id"] for c in clean if not c["reason"].strip()],
       "reviewer_ids": dict(Counter(c["reviewer"] for c in clean)), "timestamps": dict(Counter(c["timestamp"] for c in clean)),
       "label_counts": dict(Counter(c["label"] for c in clean)), "normalizations": log,
       "timestamp_note": "All rows carry one identical timestamp. It is a single session time entered by the reviewer, "
                         "not a measured completion time for each item."}
with open(H / "reviewer_R1_normalized.csv", "w", newline="", encoding="utf-8") as fh:   # derived import; reasons untouched
    w = csv.DictWriter(fh, fieldnames=list(clean[0])); w.writeheader(); w.writerows(clean)

P = {json.loads(l)["id"]: json.loads(l) for l in open(R / "eval/runs/test-haiku/predictions.jsonl")}
items = {json.loads(l)["id"]: json.loads(l) for l in open(R / "eval/data/test.jsonl")}
SYS = ["direct_1", "direct_3", "taxonomy_1", "taxonomy_3", "pipeline_noguard", "pipeline", "pipeline_noground"]
joined = []
for c in clean:
    k = key[c["review_id"]]; iid = k["item_id"]; p = P[iid]
    joined.append({"review_id": c["review_id"], "item_id": iid, "family": k["family"], "slice": items[iid]["slice"],
                   "original_label": k["original_label"], "original_subtype": k["subtype"],
                   "human_label": c["label"], "human_binary": "supported" if c["label"] == "supported" else
                   ("ambiguous" if c["label"] == "ambiguous" else "not_supported"),
                   "human_reason": c["reason"], "reviewer": c["reviewer"],
                   **{s: p[s] for s in SYS}, "pipeline_reasons": p.get("pipeline_reasons")})
(H / "joined_items.json").write_text(json.dumps(joined, indent=1, ensure_ascii=False))


def wilson(k, n, z=1.96):
    if not n:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(max(0, (c - h) / d), 3), round(min(1, (c + h) / d), 3)]


def kappa(pairs):
    n = len(pairs); po = sum(a == b for a, b in pairs) / n; labs = {x for p in pairs for x in p}
    pe = sum((sum(a == l for a, _ in pairs) / n) * (sum(b == l for _, b in pairs) / n) for l in labs)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


amb = [j for j in joined if j["human_label"] == "ambiguous"]
scored = [j for j in joined if j["human_label"] != "ambiguous"]
trans = Counter((j["original_label"], j["human_label"]) for j in joined)
bin_pairs = [(j["original_label"], j["human_binary"]) for j in scored]
agree = sum(a == b for a, b in bin_pairs)
# three-way: original items carry a subtype; only 'contradicted' subtype maps to a three-way label. Others are 'not_established'.
def orig3(j):
    return "supported" if j["original_label"] == "supported" else ("contradicted" if j["original_subtype"] == "contradicted" else "not_established")
three_pairs = [(orig3(j), j["human_label"]) for j in scored]
res = {"validation": val, "coverage": {"reviewed": len(joined), "of_subset": 30, "of_heldout": 117, "ambiguous": len(amb),
                                         "families_in_subset": len({j["family"] for j in joined})},
       "original_to_human_transition": {f"{a} -> {b}": n for (a, b), n in sorted(trans.items())},
       "binary_agreement": {"k": agree, "n": len(bin_pairs), "wilson95": wilson(agree, len(bin_pairs)), "cohen_kappa": kappa(bin_pairs)},
       "three_way_agreement": {"k": sum(a == b for a, b in three_pairs), "n": len(three_pairs), "cohen_kappa": kappa(three_pairs),
                               "note": "Original three-way label derived from the item author's subtype: 'contradicted' subtype -> contradicted; "
                                       "every other unsupported subtype -> not_established. The original labels were binary; this mapping is post hoc.",
                               "confusion": {f"{a} -> {b}": n for (a, b), n in sorted(Counter(three_pairs).items())}},
       "binary_disagreements": [{k: j[k] for k in ("review_id", "item_id", "original_label", "original_subtype", "human_label", "human_reason")}
                                for j in scored if j["original_label"] != j["human_binary"]],
       "three_way_disagreements": [{"item_id": j["item_id"], "original_3way": orig3(j), "human_label": j["human_label"], "human_reason": j["human_reason"]}
                                   for j in scored if orig3(j) != j["human_label"]],
       "systems": {}}
for s in SYS:
    out = {}
    for name, gold in (("original_labels", lambda j: j["original_label"]), ("human_labels", lambda j: j["human_binary"])):
        neg = [j for j in scored if gold(j) != "supported"]; pos = [j for j in scored if gold(j) == "supported"]
        fs = sum(j[s] == "supported" for j in neg); tp = sum(j[s] == "supported" for j in pos)
        out[name] = {"false_support": {"k": fs, "n": len(neg), "wilson95": wilson(fs, len(neg))},
                     "supported_recall": {"k": tp, "n": len(pos), "wilson95": wilson(tp, len(pos))},
                     "accuracy": {"k": fs * 0 + sum((j[s] == "supported") == (gold(j) == "supported") for j in scored), "n": len(scored)}}
    res["systems"][s] = out
res["full_117_original_labels_reference"] = {s: {"false_support": f"{sum(p[s]=='supported' for p in P.values() if p['label']!='supported')}/68",
                                                  "supported_recall": f"{sum(p[s]=='supported' for p in P.values() if p['label']=='supported')}/49"} for s in SYS}
res["provenance"] = {"reviewer": "R1 = the project author (single reviewer)", "design": "post-evaluation review; not part of the prospective freeze",
                     "subset": "30 of 117 held-out Experiment 1 items, drawn with a fixed seed (random.Random(30)), 13 originally supported and 17 not",
                     "concealed_in_packet": "original labels, subtypes, rationales, evidence highlights, item file names and all system predictions",
                     "inter_reviewer_reliability": "not available: one reviewer"}
(H / "RESULTS.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps({k: res[k] for k in ("coverage", "original_to_human_transition", "binary_agreement")}, indent=0))
print("3-way:", res["three_way_agreement"]["k"], "/", res["three_way_agreement"]["n"], "kappa", res["three_way_agreement"]["cohen_kappa"], res["three_way_agreement"]["confusion"])
print("validation:", {k: v for k, v in val.items() if k not in ("normalizations", "timestamp_note")}); print("normalizations:", log)
for d in res["binary_disagreements"]: print("BIN DISAGREE:", d)
for d in res["three_way_disagreements"]: print("3W:", d["item_id"], d["original_3way"], "->", d["human_label"], "|", d["human_reason"][:110])
for s in ("direct_1", "taxonomy_3", "pipeline_noguard"):
    print(s, {n: (v["false_support"]["k"], v["false_support"]["n"], v["supported_recall"]["k"], v["supported_recall"]["n"]) for n, v in res["systems"][s].items()})
