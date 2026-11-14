"""Figures from metrics.json / predictions.jsonl. usage: figures.py RUNDIR ATTACKRUNDIR OUTDIR"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

run, atk, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
M = json.load(open(run / "metrics.json"))
INK, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
FAM = {"direct": "#2a78d6", "taxonomy": "#eb6834", "pipeline": "#1baf7a"}
NAMES = {"direct_1": "Direct judge, 1 call", "direct_3": "Direct judge, 3 calls", "taxonomy_1": "Taxonomy judge, 1 call",
         "taxonomy_3": "Taxonomy judge, 3 calls", "pipeline_noguard": "Pipeline (primary)",
         "pipeline": "Pipeline + lexical guard", "pipeline_noground": "Pipeline, grounding off"}
plt.rcParams.update({"font.size": 9.5, "axes.edgecolor": GRID, "axes.labelcolor": MUT, "xtick.color": MUT,
                     "ytick.color": INK, "figure.facecolor": SURF, "axes.facecolor": SURF, "font.family": "DejaVu Sans"})
order = [s for s in NAMES if s in M["systems"]]


def panel(ax, key, title):
    for i, s in enumerate(order):
        r = M["systems"][s][key]; lo, hi = r["wilson95"]; y = len(order) - 1 - i
        col = FAM[s.split("_")[0]]
        ax.plot([lo * 100, hi * 100], [y, y], color=col, lw=2, solid_capstyle="round")
        ax.plot(r["rate"] * 100, y, "o", color=col, ms=8, mec=SURF, mew=2)
        ax.text(104, y, f"{r['k']}/{r['n']}", va="center", ha="left", color=INK, fontsize=9)
    ax.set_xlim(-2, 102); ax.set_ylim(-0.6, len(order) - 0.4); ax.set_title(title, loc="left", color=INK, fontsize=10.5)
    ax.set_xlabel("percent (dot = observed rate, bar = Wilson 95% interval)")
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)


fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
panel(a1, "false_support_rate", "False-support rate (lower is better)")
panel(a2, "supported_recall", "Supported-claim recall (higher is better)")
a1.set_yticks(range(len(order))); a1.set_yticklabels([NAMES[s] for s in reversed(order)])
fig.subplots_adjust(left=0.2, right=0.95, wspace=0.22, bottom=0.2, top=0.88)
fig.savefig(out / "fig1_rates.png", dpi=200); plt.close(fig)

# false support by failure subtype, three headline systems, small multiples (one axis each)
three = [s for s in ("direct_1", "taxonomy_3", "pipeline_noguard") if s in M["systems"]]
subs = sorted(M["systems"][three[0]]["false_support_by_subtype"])
fig, axes = plt.subplots(1, len(three), figsize=(10, 0.36 * len(subs) + 1.3), sharey=True)
for ax, s in zip(axes, three):
    d = M["systems"][s]["false_support_by_subtype"]
    for i, st in enumerate(subs):
        y = len(subs) - 1 - i; r = d[st]
        ax.barh(y, r["k"], color=FAM[s.split("_")[0]], height=0.55)
        ax.text(r["k"] + 0.08, y, f"{r['k']} of {r['n']}", va="center", color=INK, fontsize=9)
    ax.set_title(NAMES[s], loc="left", color=INK, fontsize=10.5); ax.set_xlim(0, max(3, max(v["k"] for v in d.values()) + 2))
    ax.set_xlabel("unsupported items accepted"); ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
axes[0].set_yticks(range(len(subs))); axes[0].set_yticklabels([x.replace("_", " ") for x in reversed(subs)])
fig.subplots_adjust(left=0.2, right=0.97, bottom=0.2, top=0.86, wspace=0.12)
fig.savefig(out / "fig2_by_subtype.png", dpi=200); plt.close(fig)
print("figures written to", out)
