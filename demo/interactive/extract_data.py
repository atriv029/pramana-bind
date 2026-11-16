"""Collect exactly what the interactive demo needs from the frozen artifacts. No model call."""
import base64, hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from pramana_bind import certificate as c, v3
from pravrudhi_kernel.ledger.verify import iter_events

R = Path(__file__).resolve().parents[2]
MM = json.load(open(R / "submission/metrics_master.json")); BA = json.load(open(R / "experiments/exp2b/BEFORE_AFTER.json"))
T = {t["item"]: t for t in json.load(open(R / "submission/QUALIFIER_TRANSITIONS.json"))}
CASES = {"v320": ("vitaminc", "vitaminc:5ede072ec9e77c00084d23f2_1"), "v323": ("vitaminc", "vitaminc:5ede072ec9e77c00084d23f2_2"),
         "q_supported": ("vitaminc", "vitaminc:5ed50882c9e77c000848fb28_3"), "q_unsupported": ("scicite", "scicite:row539")}
old_led, new_led = R / "experiments/exp2/ledger/ledger.jsonl", R / "experiments/exp2b/ledger/ledger.jsonl"
cert = lambda led: {e.payload["certificate"]["subject"]["item_id"]: (e.payload["certificate"], e.seq) for e in iter_events(led) if e.payload.get("kind") == "pramana_certificate"}
OLD, NEW = cert(old_led), cert(new_led)
out = {"cases": {}}
for key, (d, iid) in CASES.items():
    it = next(json.loads(l) for l in open(R / f"experiments/exp2/data/{d}_eval.jsonl") if json.loads(l)["id"] == iid)
    raw = next(json.loads(l)["text"] for l in open(R / f"experiments/exp2/runs/eval-{d}/calls.jsonl")
               if json.loads(l).get("ok") and json.loads(l)["tag"] == {"system": "N1", "item": iid, "run": 0})
    rec = v3.parse_record(raw); text = it["sources"][0]["text"]
    slim = lambda dd: {k: dd[k] for k in ("status", "reasons", "parts", "evidence_part_index", "qualifier_part_index", "evidence_located", "qualifiers_located", "rules_version")}
    out["cases"][key] = {
        "item": iid, "dataset": d, "claim": it["claim"], "source": text, "source_sha256": it["sources"][0]["sha256"], "reference_label": it["original_label"],
        "record": rec, "model": "claude-haiku-5-5",
        "python": {"corrected": slim(v3.decide_n1(rec, text)), "corrected_no_qualifiers": slim(v3.decide_n1(rec, text, use_qualifiers=False)),
                   "original": slim(v3.decide_n1(rec, text, legacy_part_index=True))},
        "certificate_original": {"id": OLD[iid][0]["id"], "rules": OLD[iid][0]["checks"]["rules_version"], "ledger": "experiments/exp2/ledger/ledger.jsonl", "seq": OLD[iid][1]},
        "certificate_corrected": {"id": NEW[iid][0]["id"], "rules": NEW[iid][0]["checks"]["rules_version"], "ledger": "experiments/exp2b/ledger/ledger.jsonl", "seq": NEW[iid][1]},
        "diagnosis": (T[iid]["mechanism"] if iid in T else None)}
# recorded audits (CLI-equivalent) of the ORIGINAL signed ledger and of a deliberately modified test copy
pub = (old_led.parent / "signer.pub").read_text().strip()
seq = OLD[CASES["v323"][1]][1]
rep = c.audit(old_led, pub)
steps = lambda r, s: [{"step": x.step, "ok": x.ok, "detail": x.detail} for x in r.steps if x.seq in (None, s) or x.step in ("hash_chain", "signature")]
tmp = Path(tempfile.mkdtemp()); shutil.copytree(old_led.parent, tmp / "ledger")
lines = (tmp / "ledger/ledger.jsonl").read_text().splitlines()
assert "based on 323 reviews" in lines[seq]
lines[seq] = lines[seq].replace("based on 323 reviews", "based on 320 reviews", 1)
(tmp / "ledger/ledger.jsonl").write_text("\n".join(lines) + "\n")
rep2 = c.audit(tmp / "ledger/ledger.jsonl", pub)
out["audit"] = {"genuine": {"ok": rep.ok, "n_events": rep.n_events, "n_certificates": rep.n_certificates, "steps": [s for s in steps(rep, seq) if True][:12],
                            "ledger": "experiments/exp2/ledger/ledger.jsonl", "seq": seq, "certificate": OLD[CASES["v323"][1]][0]["id"]},
                "modified": {"ok": rep2.ok, "steps": [{"step": x.step, "ok": x.ok, "detail": x.detail, "seq": x.seq} for x in rep2.steps][:4],
                             "what_changed": f'in ledger line {seq + 1} of a copy, "based on 323 reviews" was changed to "based on 320 reviews"'},
                "commands": ['python -m pramana_bind audit experiments/exp2/ledger/ledger.jsonl --pubkey "$(cat experiments/exp2/ledger/signer.pub)"',
                             f"cp -r experiments/exp2/ledger /tmp/modified_copy && sed -i '{seq + 1}s/based on 323 reviews/based on 320 reviews/' /tmp/modified_copy/ledger.jsonl",
                             'python -m pramana_bind audit /tmp/modified_copy/ledger.jsonl --pubkey "$(cat experiments/exp2/ledger/signer.pub)"']}
tot = lambda s, k: [sum(json.load(open(R / f"experiments/exp2b/runs/eval-{d}/metrics.json"))["systems"][s][k][x] for d in ("contractnli", "vitaminc", "scicite", "attributionbench")) for x in ("k", "n")]
out["aggregate"] = {"qualifier": MM["qualifier"]["TOTAL"], "items": MM["certificates"]["exp2_items"],
                    "binding_verdicts_changed": sum(len(BA["datasets"][d]["N1"]["changed_items"]) for d in BA["datasets"]),
                    "binding_explanations_changed": sum(BA["datasets"][d]["N1_items_with_changed_reasons"] for d in BA["datasets"]),
                    "multi_part_records": MM["certificates"]["multi_part_records"],
                    "direct": {"fs": tot("B0", "false_support"), "rec": tot("B0", "supported_recall")}, "typed": {"fs": tot("N1", "false_support"), "rec": tot("N1", "supported_recall")}}
(Path(__file__).parent / "demo_data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
a = out["cases"]; print({k: (v["python"]["corrected"]["status"], [p["status"] for p in v["python"]["corrected"]["parts"]], v["python"]["original"]["status"], [p["status"] for p in v["python"]["original"]["parts"]], v["python"]["corrected_no_qualifiers"]["status"], v["reference_label"]) for k, v in a.items()})
print(out["aggregate"]); print(out["audit"]["genuine"]["ok"], [(s["step"], s["ok"]) for s in out["audit"]["genuine"]["steps"]]); print(out["audit"]["modified"])
