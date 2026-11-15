"""Experiment 2 figure, generated from metrics.json files. usage: figures.py OUT.png RUNDIR [RUNDIR ...]"""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

out, runs = sys.argv[1], [Path(p) for p in sys.argv[2:]]
INK, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
COL = {"B0": "#2a78d6", "T": "#eb6834", "B1": "#eda100", "N1": "#1baf7a"}
NAME = {"B0": "Direct judge (B0)", "T": "Taxonomy judge (T)", "B1": "Generic structured (B1)", "N1": "Revised method (N1)"}
TITLE = {"contractnli": "ContractNLI", "vitaminc": "VitaminC", "scicite": "SciCiteVal", "attributionbench": "AttributionBench (OOD)"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUT, "xtick.color": MUT, "ytick.color": INK,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "font.family": "DejaVu Sans"})
fig, axes = plt.subplots(2, len(runs), figsize=(2.75 * len(runs) + 1.6, 4.2), sharey=True, squeeze=False)
order = ["B0", "T", "B1", "N1"]
for j, run in enumerate(runs):
    M = json.load(open(run / "metrics.json"))
    ds = run.name.split("-", 1)[1]
    for i, (key, lab) in enumerate((("false_support", "False-support rate, %"), ("supported_recall", "Supported recall, %"))):
        ax = axes[i][j]
        for k, s in enumerate(order):
            r = M["systems"][s][key]; y = len(order) - 1 - k; lo, hi = r["wilson95"]
            ax.plot([lo * 100, hi * 100], [y, y], color=COL[s], lw=2, solid_capstyle="round")
            ax.plot(r["rate"] * 100, y, "o", color=COL[s], ms=7.5, mec=SURF, mew=1.8)
            ax.text(104, y, f"{r['k']}/{r['n']}", va="center", ha="left", color=INK, fontsize=8)
        ax.set_xlim(-3, 103); ax.set_ylim(-0.6, len(order) - 0.4); ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(length=0)
        if i == 0:
            ax.set_title(f"{TITLE.get(ds, ds)} (n={M['n']})", loc="left", color=INK, fontsize=9.5)
        ax.set_xlabel(lab)
        if j == 0:
            ax.set_yticks(range(len(order))); ax.set_yticklabels([NAME[s] for s in reversed(order)])
fig.subplots_adjust(left=0.17, right=0.955, wspace=0.42, hspace=0.62, bottom=0.12, top=0.93)
fig.savefig(out, dpi=200); print("wrote", out)
