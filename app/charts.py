"""Graphiques Plotly de l'interface : même palette et mêmes règles que les figures du notebook."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from modules import config as C
from modules import bdd1_indicators as I
from app import theme as T

FONT = "Inter, system-ui, -apple-system, Segoe UI, sans-serif"

LAYOUT = dict(
    font=dict(family=FONT, size=13, color=C.ENCRE_2),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=20, t=30, b=10),
    hoverlabel=dict(bgcolor=T.NUIT, bordercolor=T.MUR, font=dict(family=FONT, size=12, color=C.ENCRE)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text="", traceorder="normal"),
    xaxis=dict(showgrid=False, linecolor=C.GRIS, ticks="outside", tickcolor=C.GRIS, zeroline=False),
    yaxis=dict(gridcolor=C.GRILLE, zeroline=False, linecolor=C.GRIS),
    separators=", ",
    # Conserve le zoom et les séries masquées par l'utilisateur quand la figure est recalculée.
    uirevision="fixe",
)

CLAIR = T.CLAIR  # éléments non sélectionnés


def habiller(fig: go.Figure, hauteur: int = 420, **kwargs) -> go.Figure:
    fig.update_layout(**LAYOUT, height=hauteur)
    fig.update_layout(**kwargs)
    return fig


def millions(v: float, d: int = 0) -> str:
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",") + " M"


# --------------------------------------------------------------------------------------
# Tendances
# --------------------------------------------------------------------------------------

def ventes_par_constructeur(df: pd.DataFrame, en_part: bool = False) -> go.Figure:
    v = df.pivot_table(index="Year", columns="Manufacturer", values="Global_Sales", aggfunc="sum", observed=True)
    v = v.reindex(columns=[c for c in C.ORDRE_CONSTRUCTEURS if c in v.columns]).fillna(0)
    if en_part:
        v = v.div(v.sum(axis=1), axis=0)
    fig = go.Figure()
    for c in v.columns:
        fig.add_trace(go.Scatter(
            x=v.index, y=v[c], name=c, mode="lines", stackgroup="un", line=dict(width=0.6, color=C.SURFACE),
            fillcolor=C.COULEURS_CONSTRUCTEUR[c],
            hovertemplate=f"<b>{c}</b> · %{{x}}<br>" + ("%{y:.1%}" if en_part else "%{y:,.0f} M") + "<extra></extra>",
        ))
    if C.ANNEE_PARTIELLE in v.index:
        fig.add_vrect(x0=C.ANNEE_PARTIELLE - 0.5, x1=C.ANNEE_PARTIELLE + 0.5, fillcolor=C.GRILLE, opacity=0.5,
                      line_width=0, annotation_text="2016 incomplète", annotation_position="top left",
                      annotation_font=dict(size=11, color=C.ENCRE_MUTED))
    habiller(fig, 430, hovermode="x unified")
    fig.update_yaxes(title="Part des ventes" if en_part else "Ventes mondiales (M)", tickformat=".0%" if en_part else ",.0f")
    fig.update_xaxes(title="Année de sortie")
    return fig


def barres_annuelles(serie: pd.Series, titre_y: str, format_hover: str, annee: int | None = None) -> go.Figure:
    def couleur(a: int) -> str:
        if a == annee:
            return C.PALETTE[1] if a != C.ANNEE_PARTIELLE else C.ENCRE_MUTED
        if a == C.ANNEE_PARTIELLE:
            return C.GRIS
        return C.PALETTE[0] if annee is None else CLAIR
    couleurs = [couleur(a) for a in serie.index]
    fig = go.Figure(go.Bar(x=serie.index, y=serie.values, marker_color=couleurs, marker_line_width=0,
                           hovertemplate="%{x}<br><b>" + format_hover + "</b><extra></extra>"))
    habiller(fig, 300, bargap=0.2, showlegend=False)
    fig.update_yaxes(title=titre_y)
    return fig


# --------------------------------------------------------------------------------------
# Plateformes, genres, régions
# --------------------------------------------------------------------------------------

def cycle_de_vie(df: pd.DataFrame, n: int = 20) -> go.Figure:
    top = df.groupby("Platform", observed=True).agg(v=("Global_Sales", "sum"), debut=("Year", "min"))
    top = top.nlargest(n, "v").sort_values("debut").index
    m = df[df["Platform"].isin(top)].pivot_table(index="Platform", columns="Year", values="Global_Sales",
                                                  aggfunc="sum", observed=True).reindex(top)
    noms = [C.PLATEFORMES[p][0] for p in m.index]
    fig = go.Figure(go.Heatmap(
        z=m.where(m > 0).to_numpy(), x=m.columns, y=noms, colorscale=[[i / 6, c] for i, c in enumerate(C.SEQ_BLEU)],
        colorbar=dict(title="M", thickness=12), hoverongaps=False, xgap=1, ygap=1,
        hovertemplate="<b>%{y}</b> · %{x}<br>%{z:,.1f} M<extra></extra>",
    ))
    habiller(fig, 560)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def barres_horizontales(serie: pd.Series, couleurs=None, format_texte=lambda v: millions(v), hauteur=None,
                        titre_x: str = "Ventes mondiales (M)") -> go.Figure:
    serie = serie.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=serie.values, y=serie.index, orientation="h", marker_color=couleurs[::-1] if couleurs is not None else C.PALETTE[0],
        text=[format_texte(v) for v in serie.values], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    ))
    habiller(fig, hauteur or max(300, 34 * len(serie) + 60), showlegend=False, bargap=0.3)
    fig.update_xaxes(title=titre_x, showgrid=True, gridcolor=C.GRILLE)
    fig.update_yaxes(showgrid=False)
    return fig


def frequence_vs_ventes(df: pd.DataFrame, focus: str | None = None) -> go.Figure:
    g = df.groupby("Genre", observed=True).agg(jeux=("Name", "size"), ventes=("Global_Sales", "sum"))
    g["pc"] = g["jeux"] / g["jeux"].sum()
    g["pv"] = g["ventes"] / g["ventes"].sum()
    g["nom"] = [C.GENRES_FR[x] for x in g.index]
    m = max(g["pc"].max(), g["pv"].max()) * 1.1
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, m], y=[0, m], mode="lines", line=dict(color=C.GRIS, width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=g["pc"], y=g["pv"], mode="markers+text", text=g["nom"], textposition="middle right",
        marker=dict(size=[18 if x == focus else 13 for x in g.index], line=dict(color=C.SURFACE, width=2),
                    color=[C.PALETTE[0] if focus is None or x == focus else CLAIR for x in g.index]),
        textfont=dict(color=[C.ENCRE if x == focus else C.ENCRE_2 for x in g.index]), showlegend=False,
        customdata=np.c_[g["jeux"], g["ventes"], g["pv"] / g["pc"]],
        hovertemplate="<b>%{text}</b><br>%{customdata[0]:,} jeux (%{x:.1%})<br>%{customdata[1]:,.0f} M (%{y:.1%})"
                      "<br>Rendement : x%{customdata[2]:.2f}<extra></extra>",
    ))
    habiller(fig, 430)
    fig.update_xaxes(title="Part des jeux du catalogue", tickformat=".0%", showgrid=True, gridcolor=C.GRILLE, range=[0, m * 1.18])
    fig.update_yaxes(title="Part des ventes mondiales", tickformat=".0%")
    return fig


def heatmap_pct(m: pd.DataFrame, colonnes: list[str], lignes: list[str], titre_barre: str, hauteur: int = 480,
                diverging: bool = False, fmt: str = ".0%") -> go.Figure:
    if diverging:
        # Une affinité nulle (genre absent d'une région après filtrage) donnerait log2(0) = -inf.
        z = np.log2(np.clip(m.to_numpy(dtype=float), 1 / 16, None))
        lim = np.abs(z).max()
        colorscale = [[0, C.DIV_BLEU], [0.5, C.DIV_NEUTRE], [1, C.DIV_ROUGE]]
        texte = [[f"{v:.2f}".replace(".", ",") for v in row] for row in m.to_numpy()]
        trace = go.Heatmap(z=z, x=colonnes, y=lignes, zmin=-lim, zmax=lim, colorscale=colorscale, text=texte,
                           texttemplate="%{text}", customdata=m.to_numpy(), xgap=2, ygap=2,
                           colorbar=dict(title=titre_barre, thickness=12, tickvals=[-2, -1, 0, 1], ticktext=["x0,25", "x0,5", "x1", "x2"]),
                           hovertemplate="<b>%{y}</b> · %{x}<br>affinité x%{customdata:.2f}<extra></extra>")
    else:
        trace = go.Heatmap(z=m.to_numpy(), x=colonnes, y=lignes, colorscale=[[i / 6, c] for i, c in enumerate(C.SEQ_BLEU)],
                           texttemplate="%{z:" + fmt + "}", xgap=2, ygap=2, colorbar=dict(title=titre_barre, thickness=12, tickformat=fmt),
                           hovertemplate="<b>%{y}</b> · %{x}<br>%{z:" + fmt + "}<extra></extra>")
    fig = go.Figure(trace)
    habiller(fig, hauteur)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top")
    return fig


def lignes(df_large: pd.DataFrame, couleurs: dict, noms: dict, titre_y: str, fmt: str = ".0%", hauteur: int = 400) -> go.Figure:
    fig = go.Figure()
    for col in df_large.columns:
        fig.add_trace(go.Scatter(x=df_large.index, y=df_large[col], name=noms.get(col, col), mode="lines",
                                 line=dict(color=couleurs.get(col, C.GRIS), width=2.5),
                                 hovertemplate=f"<b>{noms.get(col, col)}</b> · %{{x}}<br>%{{y:{fmt}}}<extra></extra>"))
    habiller(fig, hauteur, hovermode="x unified")
    fig.update_yaxes(title=titre_y, tickformat=fmt)
    return fig


# --------------------------------------------------------------------------------------
# Market Power Index et profil d'un jeu
# --------------------------------------------------------------------------------------

def decomposition_mpi(mpi: pd.DataFrame, poids: dict, n: int = 15, editeur: str | None = None,
                      composantes: dict = I.COMPOSANTES) -> go.Figure:
    top = mpi.head(n).iloc[::-1]
    total = sum(poids.values()) or 1
    fig = go.Figure()
    if editeur in top.index:
        i = list(top.index).index(editeur)
        fig.add_hrect(y0=i - 0.5, y1=i + 0.5, fillcolor=C.GRILLE, opacity=0.8, line_width=0, layer="below")
    for i, (k, label) in enumerate(composantes.items()):
        contrib = 100 * poids[k] / total * top[f"{k}_norm"]
        fig.add_trace(go.Bar(
            y=top.index, x=contrib, name=label, orientation="h", marker=dict(color=C.PALETTE[i], line=dict(color=C.SURFACE, width=1.5)),
            customdata=top[k], hovertemplate="<b>%{y}</b><br>" + label + " : %{x:.1f} pts<extra></extra>",
        ))
    fig.add_trace(go.Scatter(y=top.index, x=top["MPI"] + 1.5, mode="text", text=[f"{v:.1f}".replace(".", ",") for v in top["MPI"]],
                             textposition="middle right", showlegend=False, hoverinfo="skip",
                             textfont=dict(color=C.ENCRE, size=12, family=FONT)))
    habiller(fig, max(420, 30 * n + 120), barmode="stack", bargap=0.28)
    fig.update_xaxes(title="Market Power Index (0-100)", range=[0, 108], showgrid=True, gridcolor=C.GRILLE)
    fig.update_yaxes(showgrid=False)
    return fig


def profil_regional(parts_jeu: pd.Series, ref: pd.Series) -> go.Figure:
    regions = [C.REGION_LABELS[r] for r in C.REGIONS]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=regions, y=ref.to_numpy(), name="Profil du marché", marker_color=C.GRIS,
                         hovertemplate="%{x}<br>Marché : %{y:.1%}<extra></extra>"))
    fig.add_trace(go.Bar(x=regions, y=parts_jeu.to_numpy(), name="Ce jeu", marker_color=C.PALETTE[0],
                         text=[f"{v:.0%}".replace("%", " %") for v in parts_jeu], textposition="outside",
                         hovertemplate="%{x}<br>Ce jeu : %{y:.1%}<extra></extra>"))
    habiller(fig, 360, barmode="group", bargap=0.3, bargroupgap=0.08)
    fig.update_yaxes(tickformat=".0%", range=[0, 1.12], title="Part des ventes du titre")
    return fig


def nuage_outliers(div: pd.DataFrame, seuil: float) -> go.Figure:
    fig = go.Figure()
    normaux = div[~div["outlier"]]
    fig.add_trace(go.Scattergl(x=normaux["Global_Sales"], y=normaux["divergence"], mode="markers", name="Profil proche du marché",
                               marker=dict(size=5, color=C.GRIS, opacity=0.45), text=normaux["Name"],
                               hovertemplate="<b>%{text}</b><br>%{x:.2f} M · divergence %{y:.3f}<extra></extra>"))
    for r in C.REGIONS:
        o = div[div["outlier"] & (div["region_dominante"] == r)]
        fig.add_trace(go.Scattergl(
            x=o["Global_Sales"], y=o["divergence"], mode="markers", name=f"Outlier {C.REGION_LABELS[r]} ({len(o)})",
            marker=dict(size=8, color=C.COULEURS_REGION[r], line=dict(color=C.SURFACE, width=1)), text=o["Name"],
            customdata=np.c_[o["part_NA_Sales"], o["part_EU_Sales"], o["part_JP_Sales"], o["part_Other_Sales"]],
            hovertemplate="<b>%{text}</b><br>%{x:.2f} M · divergence %{y:.3f}<br>NA %{customdata[0]:.0%} · EU %{customdata[1]:.0%}"
                          " · JP %{customdata[2]:.0%} · Autres %{customdata[3]:.0%}<extra></extra>",
        ))
    fig.add_hline(y=seuil, line=dict(color=C.ENCRE, width=1), annotation_text=f"seuil outlier {seuil:.2f}".replace(".", ","),
                  annotation_position="bottom right", annotation_font=dict(size=11, color=C.ENCRE_2))
    habiller(fig, 500)
    fig.update_xaxes(type="log", title="Ventes mondiales du titre (M, échelle log)", showgrid=True, gridcolor=C.GRILLE,
                     tickvals=[0.3, 0.5, 1, 2, 5, 10, 20, 50, 100], ticktext=["0,3", "0,5", "1", "2", "5", "10", "20", "50", "100"])
    fig.update_yaxes(title="Divergence régionale (Jensen-Shannon)")
    return fig


COURTS = {"part_marche": "Part de marché", "leadership": "Leadership", "diversite": "Diversité",
          "constance": "Constance", "taux_hits": "Taux de hits"}
COURTS_QUALITE = COURTS | {"qualite": "Qualité perçue"}


def _rgba(hexa: str, alpha: float) -> str:
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


def radar_editeurs(mpi: pd.DataFrame, editeurs: list[str], courts: dict = COURTS) -> go.Figure:
    """Profil des composantes normalisées d'un ou deux éditeurs, face à la médiane des éditeurs classés."""
    axes = list(courts.values()) + [list(courts.values())[0]]
    fig = go.Figure()
    mediane = [mpi[f"{k}_norm"].median() for k in courts]
    fig.add_trace(go.Scatterpolar(r=mediane + mediane[:1], theta=axes, name="Médiane des éditeurs", mode="lines",
                                  line=dict(color=C.GRIS, dash="dot", width=1.5),
                                  hovertemplate="Médiane · %{theta}<br>%{r:.2f}<extra></extra>"))
    for e, couleur in zip(editeurs, [C.PALETTE[0], C.PALETTE[1]]):
        v = [float(mpi.loc[e, f"{k}_norm"]) for k in courts]
        fig.add_trace(go.Scatterpolar(r=v + v[:1], theta=axes, name=e, mode="lines+markers", fill="toself",
                                      fillcolor=_rgba(couleur, 0.15), line=dict(color=couleur, width=2.5), marker=dict(size=6),
                                      hovertemplate=f"<b>{e}</b> · %{{theta}}<br>%{{r:.2f}}<extra></extra>"))
    habiller(fig, 400, margin=dict(l=50, r=50, t=50, b=30))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 1], gridcolor=C.GRILLE, linecolor=C.GRILLE, tickfont=dict(size=10),
                                                 tickvals=[0.25, 0.5, 0.75, 1]),
                                 angularaxis=dict(gridcolor=C.GRILLE, linecolor=C.GRIS)))
    return fig


# --------------------------------------------------------------------------------------
# Deuxième base : notes Metacritic
# --------------------------------------------------------------------------------------

PRESSE, JOUEURS = C.PALETTE[0], C.PALETTE[1]


def ventes_par_note(t: pd.DataFrame, mesure: str, focus: str | None = None) -> go.Figure:
    """Barres par tranche de note : ventes médianes ou taux de hits (colonnes de `t`)."""
    en_part = mesure == "Taux_hits"
    couleurs = [PRESSE if focus is None or str(x) == focus else CLAIR for x in t.index]
    texte = [f"{v:.0%}".replace("%", " %") if en_part else millions(v, 2) for v in t[mesure]]
    fig = go.Figure(go.Bar(
        x=t.index.astype(str), y=t[mesure], marker_color=couleurs, marker_line_width=0, text=texte, textposition="outside",
        cliponaxis=False, customdata=t["Jeux"],
        hovertemplate="Note %{x}<br><b>%{text}</b><br>%{customdata:,} jeux<extra></extra>",
    ))
    habiller(fig, 380, showlegend=False, bargap=0.3)
    fig.update_xaxes(title="Note presse (Metacritic, /100)")
    fig.update_yaxes(title="Part de jeux à plus d'1 M" if en_part else "Ventes mondiales médianes (M)",
                     tickformat=".0%" if en_part else ",.1f")
    return fig


def notes_par_annee(par_an: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, nom, couleur in [("Critic_Score", "Presse", PRESSE), ("User_Score_100", "Joueurs (x10)", JOUEURS)]:
        fig.add_trace(go.Scatter(x=par_an.index, y=par_an[col], name=nom, mode="lines+markers",
                                 line=dict(color=couleur, width=2.5), marker=dict(size=6),
                                 hovertemplate=f"<b>{nom}</b> · %{{x}}<br>%{{y:.1f}}/100<extra></extra>"))
    habiller(fig, 380, hovermode="x unified")
    fig.update_yaxes(title="Note moyenne (/100)")
    fig.update_xaxes(title="Année de sortie")
    return fig


def notes_par_categorie(g: pd.DataFrame, noms: list[str], focus: str | None = None) -> go.Figure:
    """Haltères presse / joueurs par catégorie (genre, plateforme...), triées par note presse."""
    fig = go.Figure()
    for y, (p, j) in enumerate(zip(g["Presse"], g["Joueurs"])):
        fig.add_trace(go.Scatter(x=[p, j], y=[noms[y]] * 2, mode="lines", line=dict(color=C.GRIS, width=2),
                                 hoverinfo="skip", showlegend=False))
    taille = [14 if focus is None or n == focus else 9 for n in noms]
    for col, nom, couleur in [("Presse", "Presse", PRESSE), ("Joueurs", "Joueurs (x10)", JOUEURS)]:
        fig.add_trace(go.Scatter(x=g[col], y=noms, mode="markers", name=nom, text=noms, customdata=g["Jeux"],
                                 marker=dict(size=taille, color=couleur, line=dict(color=C.SURFACE, width=1.5)),
                                 hovertemplate=f"<b>%{{y}}</b><br>{nom} : %{{x:.1f}}/100<br>%{{customdata:,}} jeux notés<extra></extra>"))
    habiller(fig, max(340, 32 * len(noms) + 80))
    fig.update_xaxes(title="Note moyenne (/100)", showgrid=True, gridcolor=C.GRILLE)
    fig.update_yaxes(showgrid=False)
    return fig


def regions_par_note(profil: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for r in C.REGIONS:
        fig.add_trace(go.Bar(x=profil.index.astype(str), y=profil[r], name=C.REGION_LABELS[r], marker_color=C.COULEURS_REGION[r],
                             text=[f"{v:.0%}".replace("%", " %") if v > 0.06 else "" for v in profil[r]],
                             textposition="inside", insidetextanchor="middle", textfont=dict(color=C.SURFACE),
                             hovertemplate=f"<b>{C.REGION_LABELS[r]}</b> · note %{{x}}<br>%{{y:.1%}} des ventes<extra></extra>"))
    habiller(fig, 400, barmode="stack", bargap=0.3)
    fig.update_yaxes(title="Part moyenne des ventes du jeu", tickformat=".0%", range=[0, 1])
    fig.update_xaxes(title="Note presse (Metacritic, /100)")
    return fig
