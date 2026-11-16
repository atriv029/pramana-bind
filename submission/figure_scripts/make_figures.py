"""Empirical figures. Every value is read from a result file; the exact data behind each figure is written to
submission/figure_data/<figure>.json. Run: python submission/figure_scripts/make_figures.py"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from style import *  # noqa

FD = ROOT / "submission/figure_data"; FD.mkdir(exist_ok=True)
M = {d: json.load(open(ROOT / f"experiments/exp2b/runs/eval-{d}/metrics.json")) for d in DS}
MM = json.load(open(ROOT / "submission/metrics_master.json"))
dump = lambda name, obj: (FD / f"{name}.json").write_text(json.dumps(obj, indent=1))
ORDER = ["B0", "T", "B1", "N1"]

# ---------------- Figure 2: comparative performance -------------------------------------------------------------
data = {"source": "experiments/exp2b/runs/eval-*/metrics.json (rules N1/3.2, B1/1.1)", "rates": {}, "paired_N1_minus_B0": {}, "families": {}}
fig = plt.figure(figsize=(7.1, 5.0))
gs = fig.add_gridspec(3, 4, height_ratios=[1, 1, 0.82], hspace=0.95, wspace=0.16, left=0.2, right=0.985, top=0.875, bottom=0.085)
for j, d in enumerate(DS):
    data["rates"][d] = {}; data["families"][d] = M[d]["families"]
    for i, (key, lab) in enumerate((("false_support", "Unsupported claims accepted (%)"), ("supported_recall", "Supported claims accepted (%)"))):
        ax = fig.add_subplot(gs[i, j])
        for k, s in enumerate(ORDER):
            r = M[d]["systems"][s][key]; y = len(ORDER) - 1 - k; nm, col, mk = METHOD[s]; lo, hi = r["wilson95"]
            ax.plot([lo * 100, hi * 100], [y, y], color=col, lw=1.6, solid_capstyle="round", alpha=0.9)
            ax.plot(r["rate"] * 100, y, mk, color=col, ms=6, mec=WHITE, mew=1.0)
            ax.text(138, y + 0.02, f"{r['k']}/{r['n']}", va="center", ha="right", fontsize=7.2, color=NAVY, family="IBM Plex Mono")
            data["rates"][d].setdefault(s, {})[key] = r
        ax.set_xlim(-3, 139); ax.set_ylim(-0.6, len(ORDER) - 0.4); clean(ax); ax.set_xticks([0, 50, 100])
        ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([METHOD[s][0] for s in reversed(ORDER)] if j == 0 else [])
        if i == 0:
            ax.set_title(f"{DSNAME[d]}\n", fontsize=9.0); ax.text(0.5, 1.04, f"n = {M[d]['n']} · {M[d]['families']} groups", transform=ax.transAxes, ha="center", fontsize=7.6, color=SLATE)
        if j == 0:
            fig.text(0.012, ax.get_position().y1 + (0.075 if i == 0 else 0.022), "A  False-support rate (lower is better)" if i == 0 else "B  Supported recall (higher is better)",
                     fontsize=9.3, fontweight="bold", ha="left", va="bottom")
        ax.set_xlabel(lab if j == 0 else "", fontsize=7.8, loc="left")
    ax = fig.add_subplot(gs[2, j])
    pv = M[d]["paired_vs_N1"]["N1 minus B0"]; data["paired_N1_minus_B0"][d] = pv
    for y, (key, col, lab) in enumerate((("supported_recall", NAVY, "recall"), ("false_support", RED, "false support"))):
        v = pv[key]; ax.plot([v["ci95"][0] * 100, v["ci95"][1] * 100], [y, y], color=col, lw=1.6, solid_capstyle="round")
        ax.plot(v["diff"] * 100, y, "o", color=col, ms=5.5, mec=WHITE, mew=1.0)
        ax.text(v["ci95"][1] * 100 + 2.5, y, f"{v['diff'] * 100:+.0f}", va="center", fontsize=7.6, family="IBM Plex Mono", color=col)
    ax.axvline(0, color=SLATE, lw=0.8); ax.set_xlim(-45, 22); ax.set_ylim(-0.7, 1.7); clean(ax)
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Recall", "False support"] if j == 0 else [])
    ax.set_xlabel("percentage points" if j == 0 else "", fontsize=7.8, loc="left")
    if j == 0:
        fig.text(0.012, ax.get_position().y1 + 0.022, "C  Paired difference, typed record minus direct judge (95% interval, bootstrap over source groups)",
                 fontsize=9.3, fontweight="bold", ha="left", va="bottom")
save(fig, "fig2_performance"); dump("fig2_performance", data)

# ---------------- Figure 3: qualifier enforcement, paired item transitions ---------------------------------------
q = {d: MM["qualifier"][d] for d in DS}; mech = json.load(open(FD / "qualifier_mechanisms.json"))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.1, 2.95), gridspec_kw={"width_ratios": [1.0, 1.25], "wspace": 0.75, "left": 0.16, "right": 0.985, "top": 0.70, "bottom": 0.16})
ys = np.arange(len(DS))[::-1]
a1.barh(ys + 0.19, [q[d]["supported_gold_newly_accepted"] for d in DS], height=0.34, color=NAVY, label="supported claims regained")
a1.barh(ys - 0.19, [q[d]["unsupported_gold_newly_accepted"] for d in DS], height=0.34, color=RED, label="unsupported claims admitted")
for y, d in zip(ys, DS):
    a1.text(q[d]["supported_gold_newly_accepted"] + 0.3, y + 0.19, str(q[d]["supported_gold_newly_accepted"]), va="center", fontsize=8, family="IBM Plex Mono")
    a1.text(q[d]["unsupported_gold_newly_accepted"] + 0.3, y - 0.19, str(q[d]["unsupported_gold_newly_accepted"]), va="center", fontsize=8, family="IBM Plex Mono", color=RED)
a1.set_yticks(ys); a1.set_yticklabels([DSNAME[d] for d in DS]); a1.set_xlim(0, 16); clean(a1)
a1.set_xlabel("items whose outcome changes", fontsize=7.8, loc="left")
a1.legend(frameon=False, loc="lower left", bbox_to_anchor=(-0.03, 0.99), fontsize=7.6, handlelength=1.0, borderaxespad=0.1, ncol=1)
fig.text(0.012, 0.955, "A  What switching the check off changes", fontsize=9.5, fontweight="bold", va="top")
rows = ["exception or duration clause applied to a default-rule claim", "incidental detail treated as a blocking condition",
        "source genuinely restricts or hedges the statement", "subject identification treated as a condition", "unresolved"]
short = ["Exception or duration clause\napplied to a default rule", "Incidental detail treated\nas a blocking condition", "Source genuinely restricts\nor hedges the statement",
         "Subject identification\ntreated as a condition", "Unresolved"]
cols = ["gold supported (enforcement lost a correct acceptance)", "gold unsupported (enforcement prevented a false acceptance)"]
tab = np.array([[sum(t["count"] for t in mech["table"] if t["mechanism"] == r and t["outcome"] == c) for c in cols] for r in rows])
a2.set_xlim(0, 2); a2.set_ylim(0, len(rows)); a2.axis("off")
for i, r in enumerate(rows):
    y = len(rows) - 1 - i
    a2.text(-0.06, y + 0.5, short[i], ha="right", va="center", fontsize=7.8, linespacing=1.05)
    for j, col in enumerate((NAVY, RED)):
        v = tab[i, j]; alpha = 0.10 + 0.75 * v / tab.max()
        a2.add_patch(plt.Rectangle((j + 0.04, y + 0.06), 0.92, 0.88, color=col, alpha=alpha if v else 0.04, lw=0))
        a2.text(j + 0.5, y + 0.5, str(v), ha="center", va="center", fontsize=9.5, family="IBM Plex Mono", color=WHITE if alpha > 0.5 else NAVY, fontweight="bold")
a2.text(0.5, len(rows) + 0.12, "correct acceptance\nlost (37)", ha="center", va="bottom", fontsize=7.8, color=NAVY)
a2.text(1.5, len(rows) + 0.12, "false acceptance\nprevented (6)", ha="center", va="bottom", fontsize=7.8, color=RED)
fig.text(0.475, 0.955, "B  Why the check fired (AI-assisted reading, not human-reviewed)", fontsize=9.5, fontweight="bold", va="top")
save(fig, "fig3_qualifier"); dump("fig3_qualifier", {"transitions_source": "submission/metrics_master.json -> qualifier", "per_dataset": q, "mechanisms": mech})

# ---------------- Figure 5: human review --------------------------------------------------------------------------
H = json.load(open(ROOT / "experiments/human_review/RESULTS.json"))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.1, 2.75), gridspec_kw={"width_ratios": [0.9, 1.3], "wspace": 0.62, "left": 0.2, "right": 0.985, "top": 0.66, "bottom": 0.2})
cf = H["three_way_agreement"]["confusion"]; labs = ["supported", "contradicted", "not_established"]; nice = {"supported": "supported", "contradicted": "contradicted", "not_established": "not established"}
mat = np.array([[cf.get(f"{a} -> {b}", 0) for b in labs] for a in labs])
a1.set_xlim(0, 3); a1.set_ylim(0, 3); a1.axis("off")
for i, a in enumerate(labs):
    a1.text(-0.08, 2.5 - i, nice[a], ha="right", va="center", fontsize=8)
    a1.text(i + 0.5, 3.1, nice[a].replace(" ", "\n"), ha="center", va="bottom", fontsize=7.8)
    for j in range(3):
        v = mat[i, j]; ok = i == j
        a1.add_patch(plt.Rectangle((j + 0.04, 2 - i + 0.06), 0.92, 0.88, color=TEAL if ok else AMBER, alpha=(0.15 + 0.7 * v / mat.max()) if v else 0.04, lw=0))
        a1.text(j + 0.5, 2.5 - i, str(v), ha="center", va="center", fontsize=10, family="IBM Plex Mono", fontweight="bold", color=WHITE if v > 8 else NAVY)
a1.text(-0.08, 3.25, "item author's label", ha="right", fontsize=7.6, color=SLATE, va="bottom"); a1.text(1.5, 3.75, "reviewer's label", ha="center", fontsize=7.6, color=SLATE)
fig.text(0.012, 0.965, "A  Label transitions, 30 reviewed items", fontsize=9.5, fontweight="bold", va="top")
S = [("direct_1", "Direct judge, 1 call", SLATE, "o"), ("taxonomy_3", "Taxonomy judge, 3 calls", AMBER, "D"), ("pipeline_noguard", "First pipeline (Exp. 1)", TEAL, "^")]
for k, (s, nm, col, mk) in enumerate(S):
    y = len(S) - 1 - k
    for off, name, fill in ((0.13, "original_labels", col), (-0.13, "human_labels", WHITE)):
        r = H["systems"][s][name]["supported_recall"]; lo, hi = r["wilson95"]
        a2.plot([lo * 100, hi * 100], [y + off, y + off], color=col, lw=1.4, alpha=0.8); a2.plot(100 * r["k"] / r["n"], y + off, mk, color=fill, mec=col, mew=1.3, ms=6)
    r = H["systems"][s]["human_labels"]; a2.text(104, y, f"{r['supported_recall']['k']}/{r['supported_recall']['n']} accepted · {r['false_support']['k']}/{r['false_support']['n']} false", va="center", fontsize=7.4, family="IBM Plex Mono")
a2.set_yticks(range(len(S))); a2.set_yticklabels([x[1] for x in reversed(S)]); a2.set_xlim(0, 190); a2.set_xticks([0, 50, 100]); a2.set_ylim(-0.6, len(S) - 0.4); clean(a2)
a2.set_xlabel("supported claims accepted (%)   filled: author's labels · open: reviewer's labels", fontsize=7.8, loc="left")
fig.text(0.47, 0.965, "B  System scores on the same 30 items", fontsize=9.5, fontweight="bold", va="top")
save(fig, "fig5_human_review"); dump("fig5_human_review", {"source": "experiments/human_review/RESULTS.json", "three_way_confusion": cf, "binary_agreement": H["binary_agreement"],
     "systems": {s: H["systems"][s] for s, *_ in S}, "provenance": H["provenance"]})

# ---------------- Figure 7 (appendix): contrast groups ------------------------------------------------------------
cg = M["vitaminc"]["contrast_groups"]
fig, ax = plt.subplots(figsize=(3.4, 1.75)); fig.subplots_adjust(left=0.44, right=0.9, top=0.86, bottom=0.25)
for k, s in enumerate(ORDER):
    r = cg["joint_correct"][s]; y = len(ORDER) - 1 - k; nm, col, mk = METHOD[s]
    ax.plot([r["wilson95"][0] * 100, r["wilson95"][1] * 100], [y, y], color=col, lw=1.6); ax.plot(r["rate"] * 100, y, mk, color=col, ms=6, mec=WHITE, mew=1)
    ax.text(100, y, f"{r['k']}/{r['n']}", ha="right", va="center", fontsize=7.6, family="IBM Plex Mono")
ax.set_yticks(range(4)); ax.set_yticklabels([METHOD[s][0] for s in reversed(ORDER)]); ax.set_xlim(0, 100); ax.set_ylim(-0.6, 3.6); clean(ax)
ax.set_xlabel("contrast groups with every row correct (%)", fontsize=7.8, loc="left")
save(fig, "fig7_contrast"); dump("fig7_contrast", cg)

# ---------------- Figure 8 (appendix): cost and stability ----------------------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.1, 2.2), gridspec_kw={"wspace": 0.5, "left": 0.14, "right": 0.985, "top": 0.84, "bottom": 0.22})
cost = {d: M[d]["cost"] for d in DS}; w = 0.19
for k, s in enumerate(ORDER):
    nm, col, mk = METHOD[s]
    a1.bar(np.arange(4) + (k - 1.5) * w, [cost[d][s]["mean_output_tokens"] for d in DS], width=w * 0.92, color=col, label=nm)
a1.set_xticks(range(4)); a1.set_xticklabels([DSNAME[d].replace(" OOD", "").replace("Attribution", "Attr.") for d in DS]); clean(a1, "y")
a1.set_ylabel("mean output tokens per call"); a1.legend(frameon=False, fontsize=7.2, ncol=2, loc="upper right", handlelength=1, columnspacing=0.8)
a1.set_title("A  Output length by method", loc="left", x=-0.16)
st = {d: M[d]["stability_subset"] for d in DS}
for k, (s, key) in enumerate((("B0", "B0_runs_agree"), ("N1", "N1_runs_agree"))):
    nm, col, mk = METHOD[s]
    vals = [st[d][key]["k"] for d in DS]; a2.bar(np.arange(4) + (k - 0.5) * 0.34, vals, width=0.31, color=col, label=nm)
    for x, v in zip(np.arange(4) + (k - 0.5) * 0.34, vals):
        a2.text(x, v + 0.6, str(v), ha="center", fontsize=7.4, family="IBM Plex Mono")
a2.set_ylim(0, 46); a2.set_xticks(range(4)); a2.set_xticklabels([DSNAME[d].replace(" OOD", "").replace("Attribution", "Attr.") for d in DS]); clean(a2, "y")
a2.set_ylabel("items (of 40) where 3 runs agree"); a2.legend(frameon=False, fontsize=7.2, loc="upper right", ncol=2, handlelength=1)
a2.set_title("B  Repeat-run agreement (stability, not correctness)", loc="left", x=-0.16)
save(fig, "fig8_cost_stability"); dump("fig8_cost_stability", {"cost": cost, "stability": {d: {k: st[d][k] for k in ("B0_runs_agree", "N1_runs_agree")} for d in DS}})
print("figures written")

# ---------------- Figure 9 (appendix): second model ---------------------------------------------------------------
X = json.load(open(ROOT / "experiments/exp3/RESULTS.json"))
fig, axes = plt.subplots(1, 4, figsize=(7.1, 1.9), gridspec_kw={"wspace": 0.2, "left": 0.2, "right": 0.985, "top": 0.72, "bottom": 0.24})
k = 0
for d in X["datasets"]:
    for key, lab in (("false_support", "unsupported accepted (%)"), ("supported_recall", "supported accepted (%)")):
        ax = axes[k]; k += 1; y = 0; ticks = []
        for model, fill in (("haiku", True), ("sonnet", False)):
            for s in ("B0", "B1", "N1"):
                a, b = X["datasets"][d][model][s][key]; nm, col, mk = METHOD[s]
                ax.plot(100 * a / b, -y, mk, color=col if fill else WHITE, mec=col, mew=1.3, ms=6)
                ax.text(128, -y, f"{a}/{b}", ha="right", va="center", fontsize=7, family="IBM Plex Mono")
                ticks.append((-y, f"{nm.split(' (')[0]} · {'Haiku' if fill else 'Sonnet'}")); y += 1
            y += 0.5
        ax.set_xlim(-4, 130); ax.set_xticks([0, 50, 100]); ax.set_ylim(-y + 0.3, 0.7); clean(ax)
        ax.set_yticks([t[0] for t in ticks]); ax.set_yticklabels([t[1] for t in ticks] if k == 1 else [], fontsize=7.6)
        ax.set_title(f"{DSNAME[d].replace(' OOD', '')} (n={X['datasets'][d]['n']})\n{lab}", fontsize=8.2)
save(fig, "fig9_second_model"); dump("fig9_second_model", X)
