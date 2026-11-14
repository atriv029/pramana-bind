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
ap.add_argument("--note", default="")
a = ap.parse_args()
ledger = Path(a.ledger); pub = Path(a.pubkey).read_text().strip()
rep = c.audit(ledger, pub).to_dict()
want = [x for x in a.ids.split(",") if x]
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
    certs.append({"cert": {**b, "seq": ev.seq, "t": ev.t, "prev_hash": ev.prev_hash, "this_hash": ev.this_hash},
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
