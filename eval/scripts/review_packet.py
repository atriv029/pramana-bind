"""Human-review packet. Contains NO model prediction of any kind.

Writes: review_packet.html (read), review_sheet.csv (fill in), second_reviewer_ids.txt.
"""
import csv
import html
import json
import sys
from pathlib import Path

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
items = [json.loads(l) for f in sys.argv[2:] for l in open(f)]
HARD = {"misbinding", "scope_inflation", "exception_omitted", "temporal", "missing_evidence"}
second = [i["id"] for i in items if i["split"] == "test" and (
    i.get("subtype") in HARD or (i.get("averitec") or {}).get("claim_is_original"))]
(out / "second_reviewer_ids.txt").write_text("\n".join(second) + "\n")

with open(out / "review_sheet.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "split", "second_reviewer_item", "proposed_label", "reviewer_1_label", "reviewer_1_notes",
                "reviewer_2_label", "reviewer_2_notes", "adjudicated_label", "adjudication_notes"])
    for i in items:
        w.writerow([i["id"], i["split"], "yes" if i["id"] in second else "", i["label"], "", "", "", "", "", ""])
# a blind sheet for the second reviewer: no proposed label, no rationale
with open(out / "second_reviewer_blind_sheet.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "claim", "source_text", "label (supported / not_supported)", "notes"])
    for i in items:
        if i["id"] in second:
            w.writerow([i["id"], i["claim"], i["source_text"], "", ""])


def marked(i):
    t, spans = i["source_text"], sorted(i.get("evidence_spans") or [])
    o, pos = [], 0
    for s, e in spans:
        o += [html.escape(t[pos:s]), "<mark>", html.escape(t[s:e]), "</mark>"]; pos = e
    return "".join(o + [html.escape(t[pos:])])


rows = []
for n, i in enumerate(items, 1):
    rows.append(f"""<section><h3>{n}. {html.escape(i['id'])} {'<span class=t>second reviewer</span>' if i['id'] in second else ''}</h3>
<p class=k>Claim</p><p class=c>{html.escape(i['claim'])}</p>
<p class=k>Source passage <span class=s>({html.escape(i['source_locator'])})</span></p><p class=src>{marked(i)}</p>
<p class=k>Proposed label: <b>{i['label']}</b>{' · ' + i['subtype'] if i.get('subtype') else ''}</p>
<p class=r>Rationale: {html.escape(i.get('rationale', ''))}</p>
<p class=n>{html.escape(i.get('task_note', ''))} Drafting: {html.escape(i.get('drafting', ''))}</p></section>""")
(out / "review_packet.html").write_text(f"""<!doctype html><meta charset=utf-8><title>Label review packet</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:820px;margin:2rem auto;padding:0 16px;color:#1a1a1a;background:#fff}}
section{{border-top:1px solid #ccc;padding:12px 0}} .k{{font-weight:600;margin:8px 0 2px}} .c{{font-size:16px}}
.src{{white-space:pre-wrap;background:#f6f6f3;padding:10px;border-radius:6px}} mark{{background:#ffe08a}}
.s,.n{{color:#666;font-size:13px;font-weight:400}} .t{{font-size:12px;background:#234;color:#fff;padding:2px 6px;border-radius:4px}}</style>
<h1>Label review packet</h1>
<p>Task: for each item decide whether the <b>source passage alone</b> supports the claim (<i>supported</i>) or not
(<i>not_supported</i>). Scope, strength, conditions and time frame must match. Do not use outside knowledge.
Statutory items ask only what the excerpt says, not what the law currently is.</p>
<p>The highlighted span is the item author's proposed evidence. Labels and rationales were drafted by an AI assistant.
This packet contains no system predictions. Record your decisions in <code>review_sheet.csv</code>.
{len(second)} items are marked for a second reviewer, who should label them from <code>second_reviewer_blind_sheet.csv</code>
without seeing the proposed label.</p>
{''.join(rows)}""", encoding="utf-8")
print(len(items), "items;", len(second), "for second reviewer")
