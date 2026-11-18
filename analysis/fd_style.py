"""Charte graphique des figures (matplotlib), identique au thème Power BI."""
from pathlib import Path

import matplotlib as mpl

BLUE = "#2a78d6"        # couleur principale : les vols
ORANGE = "#eb6834"      # mise en avant : les retards
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e7e5e0"
SURFACE = "#fcfcfb"
NEUTRAL = "#c9c6bf"

# Ordre fixe des couleurs de catégories (validé pour le daltonisme sur paires adjacentes).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281"]

SOURCE = "Source : BTS (vols), Open-Meteo (météo), OurAirports · traitement flight-delays"


def _font():
    """Première police disponible (Segoe UI sous Windows), sans avertissement sinon."""
    from matplotlib import font_manager
    names = {f.name for f in font_manager.fontManager.ttflist}
    return next((f for f in ("Segoe UI", "Inter", "Arial") if f in names), "DejaVu Sans")


def apply():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": _font(),
        "font.size": 11,
        "axes.edgecolor": GRID,
        "axes.labelcolor": MUTED,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.titlepad": 30,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.prop_cycle": mpl.cycler(color=SERIES),
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
    })


def subtitle(ax, text):
    """Sous-titre gris : la question à laquelle répond le graphique."""
    ax.text(0, 1.02, text, transform=ax.transAxes, color=MUTED, fontsize=10.5, va="bottom")


def source(fig, text=SOURCE, y=-0.02):
    fig.text(0.01, y, text, color=MUTED, fontsize=8.5, ha="left", va="top")


def pct_axis(ax, axis="y"):
    fmt = mpl.ticker.FuncFormatter(lambda v, _: f"{v:.0f} %")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def save(fig, name, folder=Path(__file__).resolve().parent / "figures"):
    Path(folder).mkdir(exist_ok=True)
    fig.savefig(Path(folder) / f"{name}.png")
