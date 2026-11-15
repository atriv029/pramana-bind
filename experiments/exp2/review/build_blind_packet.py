"""Blind first-pass packet: claim + full allowed source + citation string only. Opaque ids, shuffled order.
No proposed label, highlight, rationale, subtype, file name or prediction. The key is written separately."""
import csv, hashlib, html, json, random, sys
from pathlib import Path
out = Path(sys.argv[1]); items = [json.loads(l) for f in sys.argv[2:] for l in open(f)]
rng = random.Random(20261115); rng.shuffle(items)
key = {}
rows = []
for n, it in enumerate(items, 1):
    oid = "R" + hashlib.sha256(("blind-v1|" + it["id"]).encode()).hexdigest()[:8].upper()
    key[oid] = it["id"]; rows.append((n, oid, it))
(out / "blind_key.DO_NOT_SHARE_WITH_REVIEWERS.json").write_text(json.dumps(key, indent=1))
with open(out / "blind_sheet.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["review_id", "label (supported / contradicted / not_established / ambiguous)", "failure_tags", "note",
                "reviewer_pseudonym", "timestamp", "policy_version"])
    for _, oid, _ in rows:
        w.writerow([oid, "", "", "", "", "", "1.1"])
body = "".join(f"<section><h3>{n}. {oid}</h3><p class=k>Claim</p><p class=c>{html.escape(it['claim'])}</p>"
               f"<p class=k>Cited as</p><p>{html.escape(it.get('citation') or '—')}</p>"
               f"<p class=k>Source context (all of it)</p><p class=src>{html.escape(it['source_text'])}</p></section>"
               for n, oid, it in rows)
(out / "blind_packet.html").write_text(f"""<!doctype html><meta charset=utf-8><title>Blind review packet</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:820px;margin:2rem auto;padding:0 16px;color:#1a1a1a;background:#fff}}
section{{border-top:1px solid #ccc;padding:12px 0}}.k{{font-weight:600;margin:8px 0 2px}}.c{{font-size:16px}}
.src{{white-space:pre-wrap;background:#f6f6f3;padding:10px;border-radius:6px}}</style>
<h1>Blind review packet</h1><p>Apply <b>ANNOTATION_POLICY.md v1.1</b>. For each item decide: supported, contradicted,
not_established, or ambiguous. Use only the text shown. Record answers in <code>blind_sheet.csv</code> against the review id.
This packet contains no proposed labels, no highlights and no system output. {len(rows)} items, in random order.</p>{body}""",
                                        encoding="utf-8")
print(len(rows), "items in blind packet")
