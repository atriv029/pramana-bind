"""Adapters from the pinned original releases into one schema. Samples are fixed here, by seed, before any system
is run. Gold labels, evidence spans and tags are stored in the item files but are never placed in a prompt."""
import csv, hashlib, json, random, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C, OUT = ROOT / "data_cache", ROOT / "experiments/exp2/data"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261115
csv.field_size_limit(10**9)
sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()
report = {}


def item(ds, rev, split, oid, fam, claim, text, orig, gold, lic, origin, evidence=(), tags=(), extra=None):
    return {"id": f"{ds}:{oid}", "dataset": ds, "dataset_revision": rev, "split": split, "source_family_id": f"{ds}:{fam}",
            "claim": claim, "sources": [{"id": "T", "text": text, "sha256": sha(text)}], "original_label": orig,
            "support_gold": gold, "evidence_gold": list(evidence), "failure_tags_gold": list(tags),
            "annotation_origin": origin, "license_reference": lic, **(extra or {})}


def write(name, rows):
    p = OUT / f"{name}.jsonl"
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    report[name] = {"items": len(rows), "families": len({r["source_family_id"] for r in rows}),
                    "labels": dict(Counter(r["support_gold"] for r in rows)),
                    "source_chars_max": max(len(r["sources"][0]["text"]) for r in rows),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


# ---- ContractNLI -----------------------------------------------------------------------------------------
CN_REV = "gh-pages@eced6528dd3c1d14d73f9a87df8f7bdbc03126f9 (resources/contract-nli.zip)"
CN_MAP = {"Entailment": "supported", "Contradiction": "contradicted", "NotMentioned": "not_established"}
def contractnli(split, n_docs):
    d = json.load(open(C / f"contract-nli/contract-nli/{split}.json"))
    docs = sorted(d["documents"], key=lambda x: x["id"])
    random.Random(SEED).shuffle(docs)
    rows = []
    for doc in docs[:n_docs]:
        for hid, ann in sorted(doc["annotation_sets"][0]["annotations"].items()):
            spans = [doc["text"][doc["spans"][i][0]:doc["spans"][i][1]] for i in ann["spans"]]
            rows.append(item("contractnli", CN_REV, split, f"{doc['id']}-{hid}", doc["id"], d["labels"][hid]["hypothesis"],
                             doc["text"], ann["choice"], CN_MAP[ann["choice"]], "CC BY 4.0 (LICENSE and TERMS in the archive)",
                             "ContractNLI annotators (Koreeda & Manning 2021)", evidence=spans, extra={"hypothesis_id": hid}))
    return rows
write("contractnli_dev", contractnli("dev", 3)); write("contractnli_eval", contractnli("test", 12))

# ---- VitaminC --------------------------------------------------------------------------------------------
VC_REV = "tals/vitaminc@be6febb761b0b2807687e61e0b5282e459df2fa0"
VC_MAP = {"SUPPORTS": "supported", "REFUTES": "contradicted", "NOT ENOUGH INFO": "not_established"}
def vitaminc(split, n_cases):
    groups = defaultdict(list)
    for l in open(C / f"tals/vitaminc/{split}.jsonl"):
        r = json.loads(l); groups[r["case_id"]].append(r)
    # contrast groups only: at least two rows and at least two different labels
    ids = sorted(k for k, v in groups.items() if len(v) >= 2 and len({x["label"] for x in v}) >= 2)
    random.Random(SEED).shuffle(ids)
    rows = []
    for cid in ids[:n_cases]:
        for r in groups[cid]:
            rows.append(item("vitaminc", VC_REV, split, r["unique_id"], cid, r["claim"], r["evidence"], r["label"],
                             VC_MAP[r["label"]], "CC BY-SA 3.0 (dataset card)", "VitaminC (Schuster et al. 2021)",
                             extra={"page": r.get("page"), "revision_type": r.get("revision_type")}))
    report[f"vitaminc_{split}_population"] = {"cases_total": len(groups), "contrast_cases": len(ids)}
    return rows
write("vitaminc_dev", vitaminc("dev", 20)); write("vitaminc_eval", vitaminc("test", 70))

# ---- SciCiteVal (evaluation only; no development use) -----------------------------------------------------
SC_REV = "birdie0111/SciCiteVal@d0bcba167856c634237ee87afc564085ae3417b1"
exp = list(csv.DictReader(open(C / "birdie0111/SciCiteVal/experiment_dataset.tsv", encoding="utf-8"), delimiter="\t"))
qasa = list(csv.DictReader(open(C / "birdie0111/SciCiteVal/Qasa_annotated.tsv", encoding="utf-8"), delimiter="\t"))
norm = lambda s: " ".join((s or "").split())
by_text = {}
for qr in qasa:  # join on verified content, never on row order
    for col in ("Composition", "Modified_composition", "Twisted_composition"):
        t = norm(qr[col])
        if t and t != "None":
            by_text.setdefault((t, norm(qr["Cited_content"])), qr)
SC_MAP = {"Correct": "supported", "Incorrect": "not_supported", "Unrelated": "not_supported"}
fam_rows, unjoined = defaultdict(list), Counter()
for i, r in enumerate(exp):
    qr = by_text.get((norm(r["Citation_context"]), norm(r["Cited_content"])))
    if qr is None:
        unjoined[r["Label"]] += 1
    fam = qr["Qasa_paper_id"] if qr else "content-" + sha(norm(r["Cited_content"]))[:10]
    fam_rows[fam].append((i, r, qr))
report["scicite_join"] = {"rows": len(exp), "labels": dict(Counter(r["Label"] for r in exp)), "not_joined_to_qasa": dict(unjoined)}
fams = sorted(fam_rows); random.Random(SEED).shuffle(fams)
rows, want = [], {"Correct": 60, "Incorrect": 60, "Unrelated": 40}
have = Counter()
for fam in fams:  # whole families until each label quota is met; quota applies per label
    for i, r, qr in fam_rows[fam]:
        if have[r["Label"]] >= want[r["Label"]]:
            continue
        have[r["Label"]] += 1
        rows.append(item("scicite", SC_REV, "train (the only split; reserved for evaluation)", f"row{i}", fam,
                         r["Citation_context"], r["Cited_content"], r["Label"], SC_MAP[r["Label"]], "CC BY 4.0 (dataset card)",
                         "SciCiteVal: Correct/Incorrect adapted from QASA with human-written distortions; Unrelated collected separately",
                         tags=[r["Twist_category"].strip()] if r["Twist_category"].strip() else [],
                         extra={"qasa_id": qr["Qasa_id"] if qr else None}))
write("scicite_eval", rows)

# ---- AttributionBench ------------------------------------------------------------------------------------
AB_REV = "osunlp/AttributionBench@62569e644f4186606f54f742178a4517431b42e1 (subset_balanced)"
AB_MAP = {"attributable": "supported", "not attributable": "not_supported"}
def attrbench(fname, split, n):
    allr = [json.loads(l) for l in open(C / f"osunlp/AttributionBench/{fname}.jsonl")]
    by = defaultdict(list)
    for r in allr:
        by[r["src_dataset"]].append(r)
    rows = []
    for src in sorted(by):  # proportional by constituent dataset
        rs = sorted(by[src], key=lambda x: str(x["id"])); random.Random(SEED).shuffle(rs)
        for r in rs[:round(n * len(by[src]) / len(allr))]:
            text = "\n\n".join(r["references"])
            claim = (f"[Question being answered: {r['question']}] " if r.get("question") else "") + r["claim"]
            rows.append(item("attributionbench", AB_REV, split, f"{src}-{r['id']}", f"{src}-{sha(text)[:10]}", claim, text,
                             r["attribution_label"], AB_MAP[r["attribution_label"]], "Apache-2.0 (dataset card); constituents vary",
                             f"AttributionBench constituent {src}; label applies to the whole reference bundle",
                             extra={"src_dataset": src}))
    return rows
write("attributionbench_dev", attrbench("dev_all_subset_balanced", "dev", 40))
write("attributionbench_eval", attrbench("test_ood_all_subset_balanced", "test_ood", 150))

# ---- contamination check: exact claim+source overlap between any dev and any eval file --------------------
key = lambda r: (norm(r["claim"]), r["sources"][0]["sha256"])
files = {p.stem: [json.loads(l) for l in open(p)] for p in OUT.glob("*.jsonl")}
dev_keys = {key(r) for n, rs in files.items() if n.endswith("_dev") for r in rs}
dev_src = {r["sources"][0]["sha256"] for n, rs in files.items() if n.endswith("_dev") for r in rs}
report["overlap_dev_eval"] = {n: {"same_claim_and_source": sum(key(r) in dev_keys for r in rs),
                                  "same_source_text": sum(r["sources"][0]["sha256"] in dev_src for r in rs)}
                              for n, rs in files.items() if n.endswith("_eval")}
(OUT / "ADAPT_REPORT.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
