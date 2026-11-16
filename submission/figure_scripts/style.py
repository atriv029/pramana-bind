"""Shared figure design system. Fonts: Source Sans 3 (labels), IBM Plex Mono (identifiers); SIL OFL, bundled in submission/fonts."""
import glob
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
for f in glob.glob(str(ROOT / "submission/fonts/*.ttf")):
    font_manager.fontManager.addfont(f)
NAVY, TEAL, VIOLET, AMBER, RED, SLATE, LIGHT, WHITE = "#17354B", "#087F83", "#7563A6", "#B7791F", "#B7464A", "#64748B", "#EDF2F5", "#FFFFFF"
GRID = "#D5DEE4"
# method encoding: colour + marker + name, the same everywhere. Red is reserved for errors / unsupported acceptance.
METHOD = {"B0": ("Direct judge (B0)", SLATE, "o"), "T": ("Taxonomy judge (T)", AMBER, "D"),
          "B1": ("Generic structured (B1)", VIOLET, "s"), "N1": ("Typed record (N1)", TEAL, "^")}
DSNAME = {"contractnli": "ContractNLI", "vitaminc": "VitaminC", "scicite": "SciCiteVal", "attributionbench": "AttributionBench OOD"}
DS = list(DSNAME)
plt.rcParams.update({
    "font.family": "Source Sans 3", "font.size": 8.5, "axes.titlesize": 9.5, "axes.titleweight": "semibold", "axes.labelsize": 8.5,
    "xtick.labelsize": 8, "ytick.labelsize": 8.5, "legend.fontsize": 8, "axes.edgecolor": GRID, "axes.labelcolor": NAVY,
    "xtick.color": SLATE, "ytick.color": NAVY, "text.color": NAVY, "axes.titlecolor": NAVY, "figure.facecolor": WHITE,
    "axes.facecolor": WHITE, "axes.linewidth": 0.8, "pdf.fonttype": 42, "svg.fonttype": "none", "axes.spines.top": False,
    "axes.spines.right": False, "figure.dpi": 100, "savefig.dpi": 300})


def clean(ax, grid="x"):
    ax.grid(axis=grid, color=GRID, lw=0.7); ax.set_axisbelow(True); ax.tick_params(length=0)
    for sp in ("left",) if grid == "x" else ("bottom",):
        ax.spines[sp].set_visible(False)


def panel(ax, letter, x=-0.02, y=1.08):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=10.5, fontweight="bold", va="bottom", ha="right", color=NAVY)


def save(fig, name):
    out = ROOT / "submission/figures"
    out.mkdir(exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
