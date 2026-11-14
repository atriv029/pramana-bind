"""Read a filled review_sheet.csv; report agreement and write reviewed labels.
usage: apply_review.py review_sheet.csv OUT.json"""
import csv
import json
import sys

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
r1 = [r for r in rows if r["reviewer_1_label"].strip()]
both = [r for r in rows if r["reviewer_1_label"].strip() and r["reviewer_2_label"].strip()]


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    labs = {x for p in pairs for x in p}
    pe = sum((sum(a == l for a, _ in pairs) / n) * (sum(b == l for _, b in pairs) / n) for l in labs)
    return None if pe == 1 else (po - pe) / (1 - pe)


out = {
    "reviewed_by_reviewer_1": len(r1),
    "reviewer_1_agrees_with_proposed": sum(r["reviewer_1_label"].strip() == r["proposed_label"] for r in r1),
    "double_reviewed": len(both),
    "reviewers_agree": sum(r["reviewer_1_label"].strip() == r["reviewer_2_label"].strip() for r in both),
    "cohen_kappa": kappa([(r["reviewer_1_label"].strip(), r["reviewer_2_label"].strip()) for r in both]),
    "disagreements": [r["id"] for r in both if r["reviewer_1_label"].strip() != r["reviewer_2_label"].strip()],
    "changed_from_proposed": [r["id"] for r in r1 if (r["adjudicated_label"].strip() or r["reviewer_1_label"].strip()) != r["proposed_label"]],
    "final_labels": {r["id"]: (r["adjudicated_label"].strip() or r["reviewer_1_label"].strip() or r["proposed_label"]) for r in rows},
}
json.dump(out, open(sys.argv[2], "w"), indent=1)
print({k: v for k, v in out.items() if k != "final_labels"})
