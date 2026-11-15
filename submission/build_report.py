"""Build submission/report.html and submission/CLAIMS.md from result files. Every number in the report is read
from a metrics file here; none is typed in. Run: python submission/build_report.py"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
E1 = json.load(open(R / "eval/runs/test-haiku/metrics.json"))
A1 = json.load(open(R / "eval/runs/attacktest-haiku/metrics.json"))
RP = json.load(open(R / "experiments/exp1/diagnostic_replay.json"))
ET = json.load(open(R / "experiments/exp1/error_table.json"))
DS = ["contractnli", "vitaminc", "scicite", "attributionbench"]
NAME = {"contractnli": "ContractNLI", "vitaminc": "VitaminC", "scicite": "SciCiteVal", "attributionbench": "AttributionBench (OOD)"}
M = {d: json.load(open(R / f"experiments/exp2/runs/eval-{d}/metrics.json")) for d in DS}
claims = []


def c(text, value, src):
    claims.append((text, str(value), src)); return value


def fr(d, s, key):
    r = M[d]["systems"][s][key]; c(f"{NAME[d]} {s} {key}", f"{r['k']}/{r['n']}", f"experiments/exp2/runs/eval-{d}/metrics.json → systems.{s}.{key}")
    return f"{r['k']}/{r['n']}"


def pct(d, s, key):
    r = M[d]["systems"][s][key]; return f"{100 * r['rate']:.0f}%"


def acc(d, s):
    if not M[d]["three_way_gold"]:
        return "—"
    v = M[d]["systems"][s]["accuracy_3way"]["rate"]; c(f"{NAME[d]} {s} three-way accuracy", v, f"experiments/exp2/runs/eval-{d}/metrics.json → systems.{s}.accuracy_3way")
    return f"{v:.3f}"


def diff(d, other, key):
    v = M[d]["paired_vs_N1"][f"N1 minus {other}"][key]
    c(f"{NAME[d]} N1 minus {other} {key}", f"{v['diff']} {v['ci95']}", f"experiments/exp2/runs/eval-{d}/metrics.json → paired_vs_N1")
    return f"{100 * v['diff']:+.0f} pts [{100 * v['ci95'][0]:+.0f}, {100 * v['ci95'][1]:+.0f}]"


SYS = [("B0", "Direct judge (B0)"), ("T", "Taxonomy judge (T)"), ("B1", "Generic structured (B1)"), ("N1", "<b>Revised method (N1)</b>"),
       ("N1_noqual", "N1, qualifiers ignored"), ("N1_noground", "N1, grounding off")]
rows = ""
for s, nm in SYS:
    rows += f"<tr><td>{nm}</td>" + "".join(
        f"<td class=n>{fr(d, s, 'false_support')}</td><td class=n>{fr(d, s, 'supported_recall')}</td>" + (f"<td class=n>{acc(d, s)}</td>" if M[d]['three_way_gold'] else "")
        for d in DS) + "</tr>"
hdr = "".join(f"<th class=n colspan={3 if M[d]['three_way_gold'] else 2}>{NAME[d]} (n={M[d]['n']})</th>" for d in DS)
sub = "".join("<th class=n>FS</th><th class=n>Rec</th>" + ("<th class=n>Acc3</th>" if M[d]["three_way_gold"] else "") for d in DS)

e1 = lambda s, k: f"{E1['systems'][s][k]['k']}/{E1['systems'][s][k]['n']}"
for s in ("direct_1", "taxonomy_3", "pipeline_noguard"):
    c(f"Exp1 {s} false support / recall", e1(s, "false_support_rate") + " ; " + e1(s, "supported_recall"), "eval/runs/test-haiku/metrics.json → systems")
q = {d: (M[d]["N1_quote_location"]["k"], M[d]["N1_quote_location"]["n"]) for d in DS}
qk, qn = sum(v[0] for v in q.values()), sum(v[1] for v in q.values())
c("N1 quotes located, four external datasets", f"{qk}/{qn}", "experiments/exp2/runs/eval-*/metrics.json → N1_quote_location")
c("Exp1 quotes located", f"{E1['pipeline']['quote_location_rate']['k']}/{E1['pipeline']['quote_location_rate']['n']}", "eval/runs/test-haiku/metrics.json → pipeline.quote_location_rate")
calls = sum(v["ok_calls"] for d in DS for v in M[d]["cost"].values()); cost = sum(v["total_cost_usd"] for d in DS for v in M[d]["cost"].values())
failed = sum(v["failed_call_records"] for d in DS for v in M[d]["cost"].values())
c("Exp2 evaluation calls / failed / cost", f"{calls} / {failed} / ${cost:.2f}", "experiments/exp2/runs/eval-*/metrics.json → cost")
cg = M["vitaminc"]["contrast_groups"]["joint_correct"]
for s in ("B0", "T", "B1", "N1"):
    c(f"VitaminC joint correctness {s}", f"{cg[s]['k']}/{cg[s]['n']}", "experiments/exp2/runs/eval-vitaminc/metrics.json → contrast_groups")
tp = M["scicite"]["accepted_by_distortion_tag"]["Tortured Phrases"]; ol = M["scicite"]["by_original_label"]
for k in ("Correct", "Incorrect", "Unrelated"):
    c(f"SciCiteVal accepted, gold {k}", {s: f"{ol[k][s]['k']}/{ol[k][s]['n']}" for s in ("B0", "T", "B1", "N1")}, "experiments/exp2/runs/eval-scicite/metrics.json → by_original_label")
c("SciCiteVal 'Tortured Phrases' accepted", {s: f"{tp[s]['k']}/{tp[s]['n']}" for s in ("B0", "B1", "N1")}, "experiments/exp2/runs/eval-scicite/metrics.json → accepted_by_distortion_tag")
stab = {d: M[d]["stability_subset"] for d in DS}
stab_txt = "; ".join(f"{NAME[d]} N1 {stab[d]['N1_runs_agree']['k']}/40, B0 {stab[d]['B0_runs_agree']['k']}/40" for d in DS)
rc = lambda d, s: stab[d]["systems"][s]["supported_recall"]
maj_txt = "; ".join(f"{NAME[d]} B0 {rc(d,'B0')['k']}→{rc(d,'B0x3')['k']} and N1 {rc(d,'N1')['k']}→{rc(d,'N1x3')['k']} of {rc(d,'B0')['n']}" for d in DS)
c("Majority of three vs one call, supported recall on 40-item subsets", maj_txt, "experiments/exp2/runs/eval-*/metrics.json → stability_subset.systems")
c("Three-run agreement on 40-item subsets", stab_txt, "experiments/exp2/runs/eval-*/metrics.json → stability_subset")
cn = M["contractnli"]["cost"]
c("ContractNLI per-call output tokens / cost, B0 vs N1", f"{cn['B0']['mean_output_tokens']} / ${cn['B0']['cost_per_call_usd']} vs {cn['N1']['mean_output_tokens']} / ${cn['N1']['cost_per_call_usd']}", "experiments/exp2/runs/eval-contractnli/metrics.json → cost")
rv = RP["variants"]; rq = rv["minus qualification_omitted"]
c("Exp1 exploratory replay without the untyped condition rule", f"FS {rq['false_support'][0]}/68, recall {rq['supported_recall'][0]}/49", "experiments/exp1/diagnostic_replay.json")
c("Exp1 error causes", ET["primary_cause_counts"], "experiments/exp1/error_table.json")
a1 = A1["systems"]
c("Attack set: unsupported accepted (all systems)", {s: f"{a1[s]['false_support_rate']['k']}/{a1[s]['false_support_rate']['n']}" for s in a1}, "eval/runs/attacktest-haiku/metrics.json")
c("Attack set: supported controls accepted", {s: f"{a1[s]['supported_recall']['k']}/{a1[s]['supported_recall']['n']}" for s in a1}, "eval/runs/attacktest-haiku/metrics.json")
tot = lambda s, k: (sum(M[d]["systems"][s][k]["k"] for d in DS), sum(M[d]["systems"][s][k]["n"] for d in DS))
T_fs = {s: tot(s, "false_support") for s, _ in SYS}; T_rc = {s: tot(s, "supported_recall") for s, _ in SYS}
c("Descriptive totals over four datasets, FS", T_fs, "sum of the four metrics.json files (not a pooled estimate)")
c("Descriptive totals over four datasets, recall", T_rc, "sum of the four metrics.json files (not a pooled estimate)")

V = dict(maj_txt=maj_txt, rows=rows, hdr=hdr, sub=sub, qk=qk, qn=qn, calls=calls, cost=f"{cost:.2f}", failed=failed, stab_txt=stab_txt,
         e1_d=e1("direct_1", "supported_recall"), e1_t=e1("taxonomy_3", "supported_recall"), e1_p=e1("pipeline_noguard", "supported_recall"),
         rq_fs=rq["false_support"][0], rq_rc=rq["supported_recall"][0],
         cn_acc=f"{acc('contractnli','N1')} vs {acc('contractnli','B0')}", cn_d=diff("contractnli", "B0", "accuracy_3way"),
         vc_acc=f"{acc('vitaminc','N1')} vs {acc('vitaminc','B0')}", vc_d=diff("vitaminc", "B0", "accuracy_3way"),
         cn_b1=diff("contractnli", "B1", "accuracy_3way"), vc_b1=diff("vitaminc", "B1", "accuracy_3way"),
         vc_fs=diff("vitaminc", "B0", "false_support"), sc_fs=diff("scicite", "B0", "false_support"), sc_rc=diff("scicite", "B0", "supported_recall"),
         cn_rc=diff("contractnli", "B0", "supported_recall"), ab_rc=diff("attributionbench", "B0", "supported_recall"),
         cnq=diff("contractnli", "N1_noqual", "supported_recall"),
         fsN=T_fs["N1"][0], fsB0=T_fs["B0"][0], fsB1=T_fs["B1"][0], fsT=T_fs["T"][0], fsNQ=T_fs["N1_noqual"][0], fsn=T_fs["N1"][1],
         rcN=T_rc["N1"][0], rcB0=T_rc["B0"][0], rcB1=T_rc["B1"][0], rcT=T_rc["T"][0], rcNQ=T_rc["N1_noqual"][0], rcn=T_rc["N1"][1],
         cgB0=f"{cg['B0']['k']}", cgT=f"{cg['T']['k']}", cgB1=f"{cg['B1']['k']}", cgN=f"{cg['N1']['k']}",
         tpB0=tp["B0"]["k"], tpN=tp["N1"]["k"], tpn=tp["N1"]["n"], incB0=ol["Incorrect"]["B0"]["k"], incN=ol["Incorrect"]["N1"]["k"],
         corB0=ol["Correct"]["B0"]["k"], corN=ol["Correct"]["N1"]["k"],
         b0tok=cn["B0"]["mean_output_tokens"], n1tok=cn["N1"]["mean_output_tokens"], b0c=cn["B0"]["cost_per_call_usd"], n1c=cn["N1"]["cost_per_call_usd"],
         exc=ET["primary_cause_counts"]["Necessary condition versus incidental detail confusion"], pol=ET["primary_cause_counts"]["Wrong polarity or negation scope"],
         ann=ET["primary_cause_counts"]["Annotation ambiguity/error"])
tpl = (Path(__file__).parent / "report_template.html").read_text(encoding="utf-8")
for k, v in V.items():
    tpl = tpl.replace("{{" + k + "}}", str(v))
assert "{{" not in tpl, tpl[tpl.index("{{"):tpl.index("{{") + 40]
(Path(__file__).parent / "report.html").write_text(tpl, encoding="utf-8")
(Path(__file__).parent / "CLAIMS.md").write_text(
    "# Claim-to-evidence table\n\nGenerated by `submission/build_report.py`. Each row is a number used in the report, its value as read, "
    "and the file and key it was read from. Metrics files are regenerated from raw model replies by `eval/scripts/score.py` and "
    "`experiments/exp2/score.py`.\n\n| Statement | Value | Source |\n|---|---|---|\n"
    + "".join(f"| {a} | {b.replace('|', '/')} | `{s}` |\n" for a, b, s in claims), encoding="utf-8")
print(len(claims), "claims;", {k: V[k] for k in ("cn_acc", "cn_d", "vc_acc", "vc_d", "fsN", "fsB0", "rcN", "rcB0", "stab_txt")})
