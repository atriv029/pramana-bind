"""Figure 1 (worked example, from a real certificate) and Figure 6 (audit boundary). HTML rendered by headless
Chromium to PDF (vector, fonts embedded) and PNG. The HTML source is the editable form of these two figures."""
import html, json, subprocess, sys
from pathlib import Path
from pravrudhi_kernel.ledger.verify import iter_events

R = Path(__file__).resolve().parents[2]; OUT = R / "submission/figures"
ITEM = "vitaminc:5ede072ec9e77c00084d23f2_2"
cert = next(e.payload["certificate"] for e in iter_events(R / "experiments/exp2b/ledger/ledger.jsonl")
            if e.payload.get("kind") == "pramana_certificate" and e.payload["certificate"]["subject"]["item_id"] == ITEM)
src = (R / "experiments/exp2b/ledger/sources" / f"{cert['texts']['T']}.txt").read_text()
rec, d = cert["record"], cert["derived"]
(R / "submission/figure_data/fig1_worked_example.json").write_text(json.dumps(
    {"certificate_id": cert["id"], "item": ITEM, "ledger": "experiments/exp2b/ledger/ledger.jsonl", "rules": cert["checks"]["rules_version"],
     "claim": cert["subject"]["claim_text"], "source": src, "record": rec, "derived": d}, indent=1))
e = html.escape
FONT = """@font-face{font-family:'Source Sans 3';font-weight:400;src:url('../fonts/source-sans-3-latin-400-normal.woff2')}
@font-face{font-family:'Source Sans 3';font-weight:400;src:url('../fonts/source-sans-3-latin-ext-400-normal.woff2');unicode-range:U+0100-02AF,U+1E00-1EFF}
@font-face{font-family:'Source Sans 3';font-weight:600;src:url('../fonts/source-sans-3-latin-600-normal.woff2')}
@font-face{font-family:'Source Sans 3';font-weight:600;src:url('../fonts/source-sans-3-latin-ext-600-normal.woff2');unicode-range:U+0100-02AF,U+1E00-1EFF}
@font-face{font-family:'IBM Plex Mono';font-weight:400;src:url('../fonts/ibm-plex-mono-latin-400-normal.woff2')}"""
CSS = FONT + """*{box-sizing:border-box}body{margin:0;font:8.6pt/1.32 'Source Sans 3',sans-serif;color:#17354B;background:#fff;width:178mm}
.m{font-family:'IBM Plex Mono',monospace;font-size:7.4pt}.lab{font-size:7.2pt;letter-spacing:.05em;text-transform:uppercase;color:#64748B;font-weight:600;margin-bottom:1.5pt}
.box{border:.8pt solid #D5DEE4;border-radius:3pt;padding:4pt 6pt;background:#fff}.model{border-left:3pt solid #7563A6;background:#F5F3FA}.mech{border-left:3pt solid #087F83;background:#EEF7F7}
.row{display:grid;gap:5pt;margin-top:5pt}.chip{display:inline-block;border-radius:8pt;padding:0 5pt;font-weight:600;font-size:7.6pt;border:.8pt solid currentColor}
.ok{color:#087F83}.bad{color:#B7464A}.neu{color:#64748B}.arrow{text-align:center;color:#64748B;font-size:9pt;line-height:1;margin:2pt 0}
table{border-collapse:collapse;width:100%}td,th{border:.6pt solid #D5DEE4;padding:2.6pt 4.5pt;vertical-align:top;text-align:left}th{background:#EDF2F5;font-weight:600;font-size:7.8pt}
.y{color:#087F83;font-weight:600}.n{color:#B7464A;font-weight:600}.a{color:#B7791F;font-weight:600}mark{background:#FBE9C8;color:inherit;padding:0 1pt}"""
parts = rec["claim"]["parts"]
def ev_for(i):
    out = ""
    for ev, loc, pi in zip(rec["evidence"], d["evidence_located"], d["evidence_part_index"]):
        if pi != i:
            continue
        out += f"""<div class="box model" style="margin-top:3pt"><div class="lab">Evidence filed by the model (reference “part {ev['part']}”)</div>
“{e(ev['quote'])}”<br>stance: <b>{e(ev['stance'])}</b> · basis: <b>{e(ev['basis']).replace('_',' ')}</b> · subject: <b>{e(ev['subject_match'])}</b></div>
<div class="box mech" style="margin-top:3pt"><div class="lab">Checked by program</div>quote found once at characters <span class="m">{loc['start']}–{loc['end']}</span> ({e(loc['match'])} match) · bound to part <span class="m">{pi + 1}</span> ({d['part_numbering'].replace('_','-')} numbering)</div>"""
    return out
def chip(s):
    return f'<span class="chip {"ok" if s == "supported" else "bad" if s == "contradicted" else "neu"}">{e(s.replace("_", " "))}</span>'
cols = "".join(f"""<div><div class="box model"><div class="lab">Claim part {i + 1} (model)</div><b>{e(p['predicate'])}</b><br>
<span style="color:#64748B">polarity {e(p['polarity'])} · quantifier {e(p['quantifier'])} · modality {e(p['modality'])}</span></div>{ev_for(i)}
<div class="arrow">▼</div><div class="box mech"><div class="lab">Rule {e(d['rules_version'])} (program)</div>
{("a located passage <b>denies</b> this part, none affirms it" if d['parts'][i]['status'] == 'contradicted' else "a located passage <b>affirms</b> this part by statement or necessary implication; none denies it; no blocking qualifier")} → {chip(d['parts'][i]['status'])}</div></div>"""
               for i, p in enumerate(parts))
hi = src
for loc in sorted(d["evidence_located"], key=lambda l: -l["start"]):
    hi = hi[:loc["start"]] + "\u0001" + hi[loc["start"]:loc["end"]] + "\u0002" + hi[loc["end"]:]
hi = e(hi).replace("\u0001", "<mark>").replace("\u0002", "</mark>")
fig1 = f"""<!doctype html><meta charset=utf-8><style>{CSS}</style><body>
<div class="row" style="grid-template-columns:1fr 1.25fr;margin-top:0"><div class="box"><div class="lab">Claim</div>{e(cert['subject']['claim_text'])}</div>
<div class="box"><div class="lab">Source (sha256 <span class="m">{cert['texts']['T'][:12]}…</span>)</div>{hi}</div></div>
<div class="arrow">▼ model extraction (one call) ▼</div>
<div class="row" style="grid-template-columns:1fr 1fr;margin-top:0">{cols}</div>
<div class="arrow">▼</div>
<div class="box mech"><div class="lab">Aggregate (program)</div>every part must be supported; one contradicted part makes the claim contradicted → {chip(d['status'])}
&nbsp; <span style="color:#64748B">certificate <span class="m">{cert['id'][-16:]}</span> · benchmark label: REFUTES</span></div>
<div style="margin-top:4pt;font-size:7.6pt;color:#64748B"><span style="border-left:3pt solid #7563A6;padding-left:4pt">violet: assigned by the model, not checked</span> &nbsp;&nbsp;
<span style="border-left:3pt solid #087F83;padding-left:4pt">teal: computed by program, recomputed on audit</span></div></body>"""
ROWS = [
 ("Quote occurs in the supplied source", "y", "Exact or whitespace-collapsed string match; zero or multiple matches refused; offsets recomputed on audit", "The supplied text is the right text"),
 ("Source text is the one the certificate was built from", "y", "SHA-256 of the stored text compared with the certificate", "The source is authoritative, complete or current"),
 ("Evidence is bound to the stated claim part", "y", "Part references resolved by a fixed rule; invalid references reported; binding stored and recomputed (rules N1/3.2)", "The model referenced the part it meant"),
 ("Decision follows from the record", "y", "Versioned rule re-run on audit; superseded versions replay under their own rule", "The rule is the right rule for the task"),
 ("Record unchanged since signing", "y", "Hash chain over ledger events; Ed25519 signature on the chain head", "Signer key obtained outside the bundle"),
 ("Ledger not rolled back or forked", "a", "Only against a checkpoint the auditor already holds", "Auditor kept an earlier head; no public log exists"),
 ("Quote means what it is filed as (stance, basis)", "n", "Not checked", "Model assignment; inverted polarity is accepted if filed so"),
 ("Quote is about the claim's subject, scope and time", "n", "Compared only through model-assigned labels", "Model assignment; a wrong-entity quote is accepted if filed so"),
 ("Qualifier is necessary rather than incidental", "n", "Not checked", "Model assignment; the largest measured source of lost recall"),
 ("No contrary evidence exists elsewhere", "n", "Not checked; nothing is retrieved", "Only the supplied context is read"),
]
sym = {"y": ("checked", "y"), "a": ("conditional", "a"), "n": ("not checked", "n")}
fig6 = f"""<!doctype html><meta charset=utf-8><style>{CSS}</style><body><table>
<tr><th style="width:31%">Property</th><th style="width:11%">Status</th><th style="width:31%">What the implementation does</th><th>What it assumes or leaves open</th></tr>
{''.join(f'<tr><td>{e(a)}</td><td class="{sym[b][1]}">{sym[b][0]}</td><td>{e(c)}</td><td>{e(dd)}</td></tr>' for a, b, c, dd in ROWS)}</table></body>"""
(R / "submission/figure_data/fig6_audit_boundary.json").write_text(json.dumps([dict(property=a, status=sym[b][0], implementation=c, assumption=dd) for a, b, c, dd in ROWS], indent=1))
for name, h in (("fig1_worked_example", fig1), ("fig6_audit_boundary", fig6)):
    (OUT / f"{name}.html").write_text(h, encoding="utf-8")
js = """const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();for(const n of process.argv.slice(2)){
const p=await b.newPage({viewport:{width:673,height:400},deviceScaleFactor:3});await p.goto('file://'+n+'.html');await p.evaluate(()=>document.fonts.ready);
const h=await p.evaluate(()=>document.body.scrollHeight);await p.setViewportSize({width:673,height:h});
await p.screenshot({path:n+'.png',fullPage:true});await p.pdf({path:n+'.pdf',width:'178mm',height:(h/96*25.4+1)+'mm',printBackground:true});}await b.close()})()"""
Path("/tmp/diag.js").write_text(js)
subprocess.run(["node", "/tmp/diag.js", str(OUT / "fig1_worked_example"), str(OUT / "fig6_audit_boundary")], check=True)
print("diagrams written;", cert["id"][-16:], d["status"], [p["status"] for p in d["parts"]], d["evidence_part_index"])

# ---- compact before/after part-binding figure (same recorded reading, two rule versions) -------------------------
DD = json.load(open(R / "demo/interactive/demo_data.json"))["cases"]["v323"]
def col(title, cls, res, note):
    rows = ""
    for i, p in enumerate(DD["record"]["claim"]["parts"]):
        evs = [ev for ev, pi in zip(DD["record"]["evidence"], res["evidence_part_index"]) if pi == i]
        rows += f"""<tr><td style="width:36%"><b>Part {i + 1}</b><br>{e(p['predicate'])}</td>
<td>{''.join(f'“{e(ev["quote"])}”<br><span style="color:#64748B">model: {e(ev["stance"])}</span>' for ev in evs) or '—'}</td>
<td style="width:24%">{chip(res['parts'][i]['status'])}</td></tr>"""
    return f"""<div class="box {cls}" style="padding:5pt 6pt"><div class="lab">{title}</div><table style="margin:2pt 0">{rows}</table>
<div>overall verdict {chip(res['status'])} &nbsp;<span style="color:#64748B">{note}</span></div></div>"""
figb = f"""<!doctype html><meta charset=utf-8><style>{CSS} td{{border:0;border-top:.6pt solid #D5DEE4;padding:3pt 4pt}} .oldrule{{border-left:3pt solid #B7464A;background:#FDF6F6}}</style><body>
<div class="box" style="margin-bottom:5pt"><span class="lab">Claim</span> {e(DD['claim'])} &nbsp; <span class="lab">Source</span> {e(DD['source'])}</div>
<div class="row" style="grid-template-columns:1fr 1fr;margin-top:0">
{col('Registered rule N1/3.1: part references read as zero-based', 'oldrule', DD['python']['original'], 'audit: pass')}
{col('Corrected rule N1/3.2: numbering resolved per record', 'mech', DD['python']['corrected'], 'audit: pass')}</div></body>"""
(R / "submission/figure_data/fig_binding_before_after.json").write_text(json.dumps({"item": DD["item"], "claim": DD["claim"], "source": DD["source"],
    "record": DD["record"], "original_N1_3.1": DD["python"]["original"], "corrected_N1_3.2": DD["python"]["corrected"],
    "certificates": [DD["certificate_original"], DD["certificate_corrected"]]}, indent=1))
(OUT / "fig_binding_before_after.html").write_text(figb, encoding="utf-8")
subprocess.run(["node", "/tmp/diag.js", str(OUT / "fig_binding_before_after")], check=True)
print("binding figure written")
