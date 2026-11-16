"""Build a single-file viewer from a real ledger. No model call, no network.

usage: build_viewer.py LEDGER.jsonl PUBKEY_FILE OUT.html [--ids id1,id2,...] [--title T]
"""
import argparse
import json
from pathlib import Path

from pramana_bind import certificate as c
from pramana_bind.status import NYAYA_TERM
from pravrudhi_kernel.ledger.verify import iter_events

ap = argparse.ArgumentParser()
ap.add_argument("ledger"); ap.add_argument("pubkey"); ap.add_argument("out")
ap.add_argument("--ids", default=""); ap.add_argument("--title", default="Pramāṇa-Bind certificates")
ap.add_argument("--note", default=""); ap.add_argument("--annot", default="")
a = ap.parse_args()
ledger = Path(a.ledger); pub = Path(a.pubkey).read_text().strip()
rep = c.audit(ledger, pub).to_dict()
want = [x for x in a.ids.split(",") if x]
ANN = json.load(open(a.annot)) if a.annot else {}
certs = []
for ev in iter_events(ledger):
    if ev.payload.get("kind") != c.PAYLOAD_KIND:
        continue
    b = ev.payload["certificate"]
    if want and b["subject"].get("item_id") not in want:
        continue
    texts = {}
    for sid, sha in b.get("texts", {}).items():
        f = c.sources_dir(ledger) / f"{sha}.txt"
        texts[sid] = f.read_text(encoding="utf-8") if f.exists() else None
    extra = {}
    if b.get("schema_version") == "3" and texts.get("T") is not None:
        from pramana_bind import v3
        legacy = b["checks"]["rules_version"] in v3.LEGACY_RULES
        cf = v3.decide_n1(b["record"], texts["T"], use_qualifiers=False, legacy_part_index=legacy)
        # computed when this page is built; NOT part of the signed record
        extra["counterfactual_no_qualifiers"] = {"status": cf["status"], "reasons": cf["reasons"]}
    extra["annotation"] = ANN.get(b["subject"].get("item_id"), {})
    certs.append({**extra, "cert": {**b, "seq": ev.seq, "t": ev.t, "prev_hash": ev.prev_hash, "this_hash": ev.this_hash},
                  "texts": texts, "audit": [s for s in rep["steps"] if s.get("cert") == b["id"]]})
if want:
    certs.sort(key=lambda x: want.index(x["cert"]["subject"]["item_id"]))
data = {"title": a.title, "note": a.note, "certs": certs, "terms": NYAYA_TERM,
        "ledger": {"file": ledger.name, "events": rep["n_events"], "ok": rep["ok"],
                   "steps": [s for s in rep["steps"] if not s.get("cert")], "pubkey": pub}}
tpl = (Path(__file__).parent / "template.html").read_text(encoding="utf-8")
Path(a.out).write_text(tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")),
                       encoding="utf-8")
print(len(certs), "certificates ->", a.out)
