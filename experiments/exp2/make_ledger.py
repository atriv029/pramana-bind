"""Build signed schema-3 certificates for the N1 system from RECORDED replies (no model call).
usage: make_ledger.py OUTDIR RUNDIR[:id,id,...] [RUNDIR ...]   (ids optional; default all items of the run)"""
import hashlib, json, shutil, sys
from pathlib import Path
from pramana_bind import certificate as c, v3

out = Path(sys.argv[1])
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
w = c.open_ledger(out / "ledger.jsonl"); n = 0
for spec in sys.argv[2:]:
    rd, _, ids = spec.partition(":")
    run = Path(rd); want = set(ids.split("|")) if ids else None
    items = {json.loads(l)["id"]: json.loads(l) for l in open(json.load(open(run / "config.json"))["items_file"])}
    calls = {}
    for l in open(run / "calls.jsonl"):
        r = json.loads(l)
        if r.get("ok") and r["tag"]["system"] == "N1":
            calls[(r["tag"]["item"], r["tag"]["run"])] = r
    for iid, it in items.items():
        if (want and iid not in want) or (iid, 0) not in calls:
            continue
        text = it["sources"][0]["text"]; rec = v3.parse_record(calls[(iid, 0)]["text"])
        if rec is None:
            continue
        runs = []
        for k in range(3):
            if (iid, k) in calls:
                rk = v3.parse_record(calls[(iid, k)]["text"]); runs.append(v3.decide_n1(rk, text)["status"] if rk else "extraction_failed")
        body = v3.make_body_v3(it["claim"], text, rec, v3.decide_n1(rec, text), model=calls[(iid, 0)]["model"], item_id=iid, run_statuses=runs)
        c.emit(body, w, {hashlib.sha256(text.encode()).hexdigest(): text}); n += 1
pub = c.generate_key(out / "signer.key"); (out / "signer.pub").write_text(pub + "\n")
c.sign_head(out / "ledger.jsonl", c.load_key(out / "signer.key"))
rep = c.audit(out / "ledger.jsonl", pub)
print(n, "certificates | audit ok:", rep.ok, "| failing steps:", [(s.step, s.seq) for s in rep.steps if not s.ok][:5])
