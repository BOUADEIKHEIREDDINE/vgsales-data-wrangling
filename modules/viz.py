"""Style graphique commun aux figures du notebook (matplotlib)."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter

from .config import (DIV_BLEU, DIV_NEUTRE, DIV_ROUGE, ENCRE, ENCRE_2, ENCRE_MUTED, FIGURES_DIR,
                     GRILLE, SEQ_BLEU, SURFACE)

CMAP_SEQ = LinearSegmentedColormap.from_list("seq_bleu", SEQ_BLEU)
CMAP_DIV = LinearSegmentedColormap.from_list("div", [DIV_BLEU, DIV_NEUTRE, DIV_ROUGE])


def appliquer_style() -> None:
    """Fond clair, grille discrète, axes fins : la donnée reste au premier plan."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "text.color": ENCRE,
        "axes.labelcolor": ENCRE_2,
        "axes.edgecolor": "#c3c2b7",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRILLE,
        "grid.linewidth": 0.7,
        "xtick.color": ENCRE_MUTED,
        "ytick.color": ENCRE_MUTED,
        "xtick.labelcolor": ENCRE_2,
        "ytick.labelcolor": ENCRE_2,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 26,
        "legend.frameon": False,
        "lines.linewidth": 2,
    })


def titre(ax, texte: str, sous_titre: str | None = None) -> None:
    """Titre à gauche + sous-titre gris qui dit comment lire le graphique."""
    ax.set_title(texte, loc="left")
    if sous_titre:
        ax.text(0, 1.02, sous_titre, transform=ax.transAxes, fontsize=9.5, color=ENCRE_2, va="bottom")


def format_millions(ax, axe: str = "y", decimales: int = 0) -> None:
    fmt = FuncFormatter(lambda v, _: fr(v, decimales) + " M")
    (ax.yaxis if axe == "y" else ax.xaxis).set_major_formatter(fmt)


def format_pct(ax, axe: str = "y", decimales: int = 0) -> None:
    fmt = FuncFormatter(lambda v, _: pct(v, decimales))
    (ax.yaxis if axe == "y" else ax.xaxis).set_major_formatter(fmt)


def norme_divergente(vmin: float, centre: float, vmax: float) -> TwoSlopeNorm:
    return TwoSlopeNorm(vmin=vmin, vcenter=centre, vmax=vmax)


def sauver(fig, nom: str) -> None:
    """Exporte la figure dans figures/ (réutilisée par le README et la soutenance)."""
    FIGURES_DIR.mkdir(exist_ok=True)
    fig.savefig(FIGURES_DIR / f"{nom}.png", bbox_inches="tight")


def fr(v: float, decimales: int = 1) -> str:
    """Nombre au format français : virgule décimale, espace pour les milliers."""
    return f"{v:,.{decimales}f}".replace(",", " ").replace(".", ",")


def pct(v: float, decimales: int = 0) -> str:
    """Pourcentage au format français : 0.123 -> '12 %'."""
    return f"{fr(v * 100, decimales)} %"


def repartir(valeurs, ecart_min: float):
    """Décale des positions d'étiquettes (en unités de données) pour qu'elles ne se chevauchent pas,
    en conservant leur ordre et en restant au plus près des valeurs d'origine."""
    import numpy as np
    valeurs = np.asarray(valeurs, dtype=float)
    ordre = np.argsort(valeurs)
    pos = valeurs[ordre].copy()
    for _ in range(50):
        for i in range(1, len(pos)):
            if pos[i] - pos[i - 1] < ecart_min:
                milieu = (pos[i] + pos[i - 1]) / 2
                pos[i - 1], pos[i] = milieu - ecart_min / 2, milieu + ecart_min / 2
    resultat = np.empty_like(pos)
    resultat[ordre] = pos
    return resultat
