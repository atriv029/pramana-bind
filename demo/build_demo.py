"""Build the demo ledger from RECORDED model output (no live call):
four held-out items re-bound from their cached extraction replies, plus one
unresolved certificate (source not located; the model is never called)."""
import json
import shutil
import sys
from pathlib import Path

from pramana_bind import certificate as c
from pramana_bind.bind import bind, bind_extractions
from pramana_bind.extract import Extraction, parse

run, out = Path(sys.argv[1]), Path(sys.argv[2])
IDS = sys.argv[3].split(",")
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
items = {json.loads(l)["id"]: json.loads(l) for l in open(run / "config.json").read() and open(json.load(open(run / "config.json"))["items_file"])}
calls = {}
for l in open(run / "calls.jsonl"):
    r = json.loads(l)
    if r.get("ok") and r["tag"]["system"] == "extract":
        calls[(r["tag"]["item"], r["tag"]["run"])] = r["text"]
w = c.open_ledger(out / "ledger.jsonl")
for iid in IDS:
    it = items[iid]
    exs = [Extraction(parse(calls[(iid, k)]), calls[(iid, k)]) for k in range(3)]
    body, texts = bind_extractions(it["claim"], it["source_text"], exs, citation_raw=it["citation"],
                                   model="claude-haiku-5-5", guard=False)
    body["subject"]["item_id"] = iid; body["id"] = c.cert_id(body)
    c.emit(body, w, texts)

def never(_):
    raise AssertionError("no model call for an unlocated source")
body, texts = bind("The tribunal held that the levy was unlawful.", None, never,
                   citation_raw="Unreported tribunal decision, 2019 (not in any index available to the system)")
body["subject"]["item_id"] = "demo-unresolved"; body["id"] = c.cert_id(body)
c.emit(body, w, texts)
pub = c.generate_key(out / "signer.key")
(out / "signer.pub").write_text(pub + "\n")
c.sign_head(out / "ledger.jsonl", c.load_key(out / "signer.key"))
print("audit ok:", c.audit(out / "ledger.jsonl", pub).ok, "| pubkey", pub)
