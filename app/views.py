"""Pages de l'interface. Chaque page reçoit le contexte : données filtrées, données complètes, journal, pages.

Fluidité : les calculs coûteux passent par app/donnees.py (cache par combinaison de filtres) et les sections
réglables sont des fragments (st.fragment) : un réglage ne réexécute que sa section, pas toute la page.
Interactivité : un clic sur un jeu (barre, point ou ligne de tableau) ouvre sa fiche dans une fenêtre.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from modules import config as C
from modules import bdd1_indicators as I
from modules import bdd2_jointure as J

from . import charts as G
from . import donnees as D

NOMS_REG = C.REGION_LABELS
GENRES_INV = {v: k for k, v in C.GENRES_FR.items()}

CONFIG_GRAPHE = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


def fr(v: float, d: int = 0) -> str:
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(v: float, d: int = 1) -> str:
    return f"{fr(v * 100, d)} %"


def entete(titre: str, sous_titre: str) -> None:
    st.markdown(f"<h1 class='titre'>{titre}</h1><p class='sous-titre'>{sous_titre}</p>", unsafe_allow_html=True)


def encart(texte: str) -> None:
    st.markdown(f"<div class='encart'>{texte}</div>", unsafe_allow_html=True)


def astuce(texte: str) -> None:
    st.markdown(f"<p class='astuce'>💡 {texte}</p>", unsafe_allow_html=True)


def tuiles(valeurs: list[tuple[str, str, str]]) -> None:
    for col, (label, valeur, aide) in zip(st.columns(len(valeurs)), valeurs):
        col.metric(label, valeur, help=aide, border=True)


def garde_vide(df: pd.DataFrame) -> bool:
    if df.empty:
        st.warning("Aucun jeu ne correspond aux filtres choisis. Élargissez la période ou les sélections dans la barre latérale.")
        return True
    return False


def graphique(fig, key: str, clic=None):
    """Graphique Plotly ; `clic(point)` est appelé quand l'utilisateur clique sur une barre ou un point."""
    if clic is None:
        return st.plotly_chart(fig, key=key, config=CONFIG_GRAPHE)
    # Plotly estompe les éléments non cliqués : la page gère elle-même la mise en évidence, on neutralise donc cet effet.
    for trace in fig.data:
        if hasattr(trace, "unselected"):
            opacite = getattr(trace.marker, "opacity", None)
            trace.unselected = dict(marker=dict(opacity=opacite if isinstance(opacite, (int, float)) else 1))
            trace.selected = dict(marker=dict(opacity=opacite if isinstance(opacite, (int, float)) else 1))
    fig.update_layout(clickmode="event+select")

    def rappel() -> None:
        points = (st.session_state.get(key) or {}).get("selection", {}).get("points", [])
        if points:
            clic(points[0])

    return st.plotly_chart(fig, key=key, config=CONFIG_GRAPHE, on_select=rappel, selection_mode="points")


def tableau(data: pd.DataFrame, key: str, clic=None, **kwargs):
    """Tableau ; `clic(ligne)` reçoit la ligne cliquée (selon l'ordre de `data`, même si l'utilisateur trie)."""
    if clic is None:
        return st.dataframe(data, key=key, **kwargs)

    def rappel() -> None:
        lignes = (st.session_state.get(key) or {}).get("selection", {}).get("rows", [])
        if lignes:
            clic(data.iloc[lignes[0]])

    return st.dataframe(data, key=key, on_select=rappel, selection_mode="single-row", **kwargs)


def suite(ctx: dict, actuelle: str) -> None:
    """Lien vers la page suivante, pour lire l'interface comme un rapport."""
    ordre = ctx["ordre"]
    i = ordre.index(actuelle)
    if i + 1 < len(ordre):
        page = ctx["pages"][ordre[i + 1]]
        st.divider()
        st.page_link(page, label=f"Page suivante : {page.title}  →", icon=page.icon)


# --------------------------------------------------------------------------------------
# Fiche d'un jeu (fenêtre ouverte par un clic, ou page Explorateur)
# --------------------------------------------------------------------------------------

def ouvrir_jeu(nom: str) -> None:
    st.session_state["_fiche"] = nom


def fiche_si_demandee(ctx: dict) -> None:
    nom = st.session_state.pop("_fiche", None)
    if nom:
        _fenetre_jeu(ctx, nom)


@st.dialog("Fiche du jeu", width="large")
def _fenetre_jeu(ctx: dict, nom: str) -> None:
    st.markdown(f"### {nom}")
    profil_jeu(ctx, nom, prefixe="dlg")
    if st.button("Ouvrir dans l'explorateur de jeux →", key="dlg_explorer"):
        D.definir("jeu_nom", nom)
        st.switch_page(ctx["pages"]["jeux"])


def profil_jeu(ctx: dict, nom: str, prefixe: str) -> None:
    df = ctx["df"]
    titres = D.titres(ctx["cle"])
    if nom not in set(titres["Name"]):
        st.info("Ce titre ne fait pas partie de la sélection filtrée.")
        return
    ref = I.profil_marche(df)
    t = titres.set_index("Name").loc[nom]
    parts = t[C.REGIONS].astype(float) / max(t[C.REGIONS].sum(), 1e-9)
    score = float(I.jensen_shannon(parts.to_numpy(), ref.to_numpy())[0])
    rang = int((titres["Global_Sales"] > t["Global_Sales"]).sum()) + 1
    tuiles([
        ("Ventes mondiales", fr(t["Global_Sales"], 2) + " M", f"{rang}e meilleure vente de la sélection"),
        ("Sortie", str(int(t["Year"])), "Première année de sortie"),
        ("Plateformes", str(int(t["n_plateformes"])), t["Plateformes"]),
        ("Divergence régionale", fr(score, 3), "0 = se vend exactement comme le marché ; 1 = maximum"),
    ])
    joint = D.joint(ctx["cle"])
    notes_jeu = joint[(joint["Name"] == nom) & joint["Note_Presse"]]
    if len(notes_jeu):
        meilleure = notes_jeu.loc[notes_jeu["Critic_Score"].idxmax()]
        joueurs = notes_jeu["User_Score_100"].dropna()
        critiques = f" ({int(meilleure['Critic_Count'])} critiques)" if pd.notna(meilleure["Critic_Count"]) else ""
        tuiles([
            ("Note presse", f"{fr(meilleure['Critic_Score'])}/100", f"Metacritic, meilleure version : {meilleure['Platform_Name']}{critiques}"),
            ("Note joueurs", f"{fr(joueurs.mean())}/100" if len(joueurs) else "–", "Moyenne des versions notées par les joueurs, ramenée sur 100"),
            ("Studio", meilleure["Developer_Main"], "Studio de développement (Metacritic)"),
            ("Classification", meilleure["Rating"], meilleure["Rating_Label"]),
        ])
    else:
        st.caption("Pas de note Metacritic pour ce titre : Metacritic couvre surtout les jeux sortis après 2000.")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        graphique(G.profil_regional(parts, ref), key=f"{prefixe}_profil")
    with c2:
        st.markdown(f"**{t['Publisher']}** · {C.GENRES_FR.get(t['Genre'], t['Genre'])}")
        exces = (parts - ref).sort_values(ascending=False)
        st.markdown(f"Région la plus sur-représentée : **{NOMS_REG[exces.index[0]]}** "
                    f"({pct(parts[exces.index[0]], 0)} des ventes contre {pct(ref[exces.index[0]], 0)} pour le marché).")
        if t["Global_Sales"] < 0.5:
            st.info("Titre sous 0,5 M : les ventes étant arrondies au centième, son profil régional est peu fiable.")
        versions = joint[joint["Name"] == nom][["Platform_Name", "Year", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales",
                                                "Critic_Score", "User_Score_100"]]
        st.dataframe(versions.rename(columns={"Platform_Name": "Plateforme", "Year": "Année", "NA_Sales": "NA", "EU_Sales": "EU",
                                              "JP_Sales": "JP", "Other_Sales": "Autres", "Global_Sales": "Total",
                                              "Critic_Score": "Presse", "User_Score_100": "Joueurs"}),
                     hide_index=True, key=f"{prefixe}_versions", column_config={
                         "Année": st.column_config.NumberColumn(format="%d"),
                         "Presse": st.column_config.NumberColumn(format="%.0f", help="Note presse Metacritic (/100)"),
                         "Joueurs": st.column_config.NumberColumn(format="%.0f", help="Note joueurs Metacritic, ramenée sur 100")})


COLONNES_JEUX = {
    "Name": "Titre", "Year": st.column_config.NumberColumn("Année", format="%d"), "Publisher": "Éditeur", "Genre": "Genre",
    "Global_Sales": st.column_config.NumberColumn("Ventes (M)", format="%.2f"), "Plateformes": "Plateformes",
}


def tableau_jeux(ctx: dict, t: pd.DataFrame, key: str, hauteur: int | str = "auto") -> None:
    """Liste de titres cliquable : une ligne ouvre la fiche du jeu."""
    t = t[["Name", "Year", "Genre", "Publisher", "Global_Sales", "Plateformes"]].assign(Genre=lambda x: x["Genre"].map(C.GENRES_FR))
    tableau(t.reset_index(drop=True), key, clic=lambda ligne: ouvrir_jeu(ligne["Name"]), hide_index=True,
            column_config=COLONNES_JEUX, height=hauteur)


# --------------------------------------------------------------------------------------
# 1. Vue d'ensemble
# --------------------------------------------------------------------------------------

def vue_ensemble(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    df = ctx["df"]
    debut, fin = int(df["Year"].min()) if len(df) else 1980, int(df["Year"].max()) if len(df) else 2016
    entete(f"Le marché mondial du jeu vidéo, {debut}-{fin}",
           f"Ventes physiques de {fr(len(df))} jeux nettoyés · source VGChartz · millions d'exemplaires")
    if garde_vide(df):
        return
    total = df["Global_Sales"].sum()
    titres = D.titres(ctx["cle"])
    top10 = df.groupby("Publisher")["Global_Sales"].sum().nlargest(10).sum() / total
    tuiles([
        ("Ventes", fr(total, 0) + " M",
         f"{pct(total / ctx['df_all']['Global_Sales'].sum(), 0)} du marché 1980-2016" if ctx["filtre_actif"] else "Exemplaires vendus, toutes régions"),
        ("Jeux", fr(len(df)), "Couples titre / plateforme"),
        ("Titres", fr(len(titres)), "Titres distincts, toutes plateformes"),
        ("Éditeurs", fr(df["Publisher"].nunique()), "Dont la modalité « Inconnu »"),
        ("Part du top 10 éditeurs", pct(top10, 0), "Concentration du marché de l'édition"),
    ])

    st.subheader("Un marché porté par les cycles de consoles")
    _ensemble_constructeurs(df)

    gauche, droite = st.columns([1.15, 1])
    with gauche:
        st.subheader("Top 10 des titres")
        t = titres.head(10)
        couleurs = [C.PALETTE[7] if p == "Nintendo" else C.GRIS for p in t["Publisher"]]
        graphique(G.barres_horizontales(t.set_index("Name")["Global_Sales"], couleurs, hauteur=420), key="ens_top",
                  clic=lambda p: ouvrir_jeu(p["y"]))
        astuce("Cliquez sur une barre pour ouvrir la fiche du jeu. Rouge : Nintendo ; les ventes additionnent toutes les plateformes.")
    with droite:
        st.subheader("Ce qu'il faut retenir")
        encart("""
        <ol>
        <li><b>Économie de blockbusters</b> : 10 % des jeux font ~59 % des ventes.</li>
        <li><b>Pic en 2008</b> (688 M), puis bascule vers le dématérialisé, absent des données.</li>
        <li><b>Sony et Nintendo</b> se partagent ~80 % des ventes de jeux.</li>
        <li><b>L'Action et le Tir</b> passent de 18 % à 45 % des ventes en 15 ans.</li>
        <li><b>Le Japon</b> achète 2,6× plus de RPG et 4× moins de jeux de tir.</li>
        <li><b>Nintendo</b> domine le Market Power Index (95/100), loin devant EA.</li>
        </ol>
        """)
        if ctx["filtre_actif"]:
            st.caption("Ces messages portent sur l'ensemble du marché 1980-2016, pas sur la sélection filtrée.")
    suite(ctx, "accueil")


@st.fragment
def _ensemble_constructeurs(df: pd.DataFrame) -> None:
    en_part = D.persistant(st.segmented_control, "ens_part", "Affichage", ["Volume", "Part de marché"], param="default", required=True,
                                   label_visibility="collapsed") == "Part de marché"
    graphique(G.ventes_par_constructeur(df, en_part), key="ens_constructeurs")
    astuce("Cliquez sur un constructeur dans la légende pour le masquer, double-cliquez pour l'isoler.")


# --------------------------------------------------------------------------------------
# 2. Tendances et plateformes
# --------------------------------------------------------------------------------------

def vue_tendances(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    df = ctx["df"]
    entete("Tendances et plateformes", "Combien de jeux, combien de ventes, et sur quelles consoles")
    if garde_vide(df):
        return
    _tendances_annuelles(ctx)

    st.subheader("Cycle de vie des plateformes")
    _tendances_cycle(df)

    st.subheader("Classement des plateformes")
    _tendances_classement(ctx)
    suite(ctx, "tendances")


def choisir_annee(point: dict) -> None:
    st.session_state["t_annee"] = int(point["x"])


@st.fragment
def _tendances_annuelles(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    df = ctx["df"]
    annuel = df.groupby("Year").agg(jeux=("Name", "size"), ventes=("Global_Sales", "sum"))
    annuel["par_jeu"] = annuel["ventes"] / annuel["jeux"]
    if st.session_state.get("t_annee") not in annuel.index:
        complet = annuel.loc[annuel.index != C.ANNEE_PARTIELLE] if len(annuel) > 1 else annuel
        st.session_state["t_annee"] = int(complet["ventes"].idxmax())
    annee = st.session_state["t_annee"]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Jeux sortis par année**")
        graphique(G.barres_annuelles(annuel["jeux"], "Nombre de jeux", "%{y:,} jeux", annee), key="t_jeux", clic=choisir_annee)
    with c2:
        st.markdown("**Ventes mondiales par année de sortie**")
        graphique(G.barres_annuelles(annuel["ventes"], "Ventes (M)", "%{y:,.0f} M", annee), key="t_ventes", clic=choisir_annee)
    astuce("Cliquez sur une année pour afficher ses meilleures ventes ci-dessous. En gris clair : 2016, année incomplète.")

    gauche, droite = st.columns([1, 1.25])
    with gauche:
        st.markdown("**Ventes moyennes par jeu**")
        graphique(G.barres_annuelles(annuel["par_jeu"], "M par jeu", "%{y:.2f} M par jeu", annee), key="t_moy", clic=choisir_annee)
        encart("Après 2011, il sort deux fois moins de jeux mais chacun vend davantage : les éditeurs concentrent leurs budgets "
               "sur quelques franchises.")
    with droite:
        a = annuel.loc[annee]
        st.markdown(f"**{annee} : {fr(a['jeux'])} jeux, {fr(a['ventes'], 0)} M d'exemplaires**")
        t = D.titres(ctx["cle"])
        tableau_jeux(ctx, t[t["Name"].isin(df.loc[df["Year"] == annee, "Name"])].head(12), key="t_top_annee", hauteur=420)
        st.caption("Les 12 titres les plus vendus de l'année (toutes plateformes). Cliquez sur une ligne pour la fiche.")


@st.fragment
def _tendances_cycle(df: pd.DataFrame) -> None:
    n_max = int(df["Platform"].nunique())
    if n_max > 8:
        D.definir("t_n", min(D.valeur("t_n"), n_max))
        n = D.persistant(st.slider, "t_n", "Nombre de plateformes", 8, n_max)
    else:
        n = n_max
    graphique(G.cycle_de_vie(df, n), key="t_cycle")


@st.fragment
def _tendances_classement(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    df = ctx["df"]
    p = df.groupby("Platform", observed=True).agg(
        Plateforme=("Platform_Name", "first"), Constructeur=("Manufacturer", "first"), Type=("Platform_Type", "first"),
        Jeux=("Name", "size"), Ventes=("Global_Sales", "sum"), Début=("Year", "min"), Fin=("Year", "max"),
    ).sort_values("Ventes", ascending=False)
    p["Part"] = p["Ventes"] / p["Ventes"].sum()
    p["Ventes par jeu"] = p["Ventes"] / p["Jeux"]
    p["Note presse"] = D.joint(ctx["cle"]).groupby("Platform", observed=True)["Critic_Score"].mean()
    p = p.reset_index()
    if st.session_state.get("t_plateforme") not in set(p["Platform"]):
        st.session_state["t_plateforme"] = p["Platform"].iloc[0]

    def choisir(ligne: pd.Series) -> None:
        st.session_state["t_plateforme"] = ligne["Platform"]

    gauche, droite = st.columns([1.5, 1])
    with gauche:
        tableau(p, "t_plateformes", clic=choisir, hide_index=True, height=460,
                column_order=["Plateforme", "Constructeur", "Type", "Jeux", "Ventes", "Part", "Ventes par jeu", "Note presse", "Début", "Fin"],
                column_config={
                    "Ventes": st.column_config.ProgressColumn("Ventes (M)", format="%.0f", min_value=0, max_value=float(p["Ventes"].max())),
                    "Part": st.column_config.NumberColumn(format="percent"),
                    "Ventes par jeu": st.column_config.NumberColumn(format="%.2f M"),
                    "Note presse": st.column_config.NumberColumn(format="%.1f", help="Note presse Metacritic moyenne des jeux notés (/100). "
                                                                 "Vide : plateforme non couverte par Metacritic."),
                    "Début": st.column_config.NumberColumn(format="%d"), "Fin": st.column_config.NumberColumn(format="%d"),
                })
        astuce("Cliquez sur une plateforme pour voir ses meilleures ventes.")
    with droite:
        code = st.session_state["t_plateforme"]
        st.markdown(f"**Meilleures ventes sur {C.PLATEFORMES[code][0]}**")
        jeux = df[df["Platform"] == code].nlargest(10, "Global_Sales").assign(Plateformes=code)
        tableau_jeux(ctx, jeux, key="t_top_plateforme", hauteur=390)


# --------------------------------------------------------------------------------------
# 3. Genres
# --------------------------------------------------------------------------------------

def choisir_genre(point: dict) -> None:
    nom = point.get("text") or point.get("y")
    if nom in GENRES_INV:
        st.session_state["g_focus"] = GENRES_INV[nom]


def vue_genres(ctx: dict) -> None:
    df = ctx["df"]
    entete("Genres", "Ce qui est produit, ce qui se vend, et comment cela évolue")
    if garde_vide(df):
        return
    _genres_zoom(ctx)

    st.subheader("Évolution de la part des genres")
    _genres_evolution(df)

    st.subheader("Qui domine chaque genre ?")
    pg = I.parts_genre(df[df["Publisher"] != "Inconnu"])
    pg = pg.loc[:, pg.notna().sum() >= 2]
    leaders = pd.DataFrame({
        "Genre": [C.GENRES_FR[g] for g in pg.columns], "Leader": pg.idxmax().to_numpy(), "Part du leader": pg.max().to_numpy(),
        "N°2": pg.apply(lambda c: c.nlargest(2).index[1]).to_numpy(), "Part du n°2": pg.apply(lambda c: c.nlargest(2).iloc[1]).to_numpy(),
    }).sort_values("Part du leader", ascending=False)
    leaders[["Part du leader", "Part du n°2"]] *= 100
    st.dataframe(leaders, hide_index=True, column_config={
        "Part du leader": st.column_config.ProgressColumn(format="%.0f %%", min_value=0, max_value=100),
        "Part du n°2": st.column_config.NumberColumn(format="%.0f %%"),
    })
    suite(ctx, "genres")


@st.fragment
def _genres_zoom(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    df = ctx["df"]
    v = df.groupby("Genre", observed=True)["Global_Sales"].sum().sort_values(ascending=False)
    if st.session_state.get("g_focus") not in v.index:
        st.session_state["g_focus"] = v.index[0]
    focus = st.session_state["g_focus"]

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**Fréquence et ventes : quels genres sur-performent ?**")
        graphique(G.frequence_vs_ventes(df, focus), key="g_scatter", clic=choisir_genre)
        st.caption("Au-dessus de la diagonale, le genre vend plus que son poids dans le catalogue.")
    with c2:
        st.markdown("**Ventes mondiales par genre**")
        noms = pd.Series(v.to_numpy(), index=[C.GENRES_FR[g] for g in v.index])
        couleurs = [C.PALETTE[0] if g == focus else G.CLAIR for g in v.index]
        graphique(G.barres_horizontales(noms, couleurs, hauteur=430), key="g_barres", clic=choisir_genre)
    astuce("Cliquez sur un genre (point ou barre) pour le détailler ci-dessous.")

    d = df[df["Genre"] == focus]
    part_v = d["Global_Sales"].sum() / df["Global_Sales"].sum()
    aff = I.affinite_genre_region(df).loc[focus]
    st.markdown(f"#### Zoom : {C.GENRES_FR[focus]}")
    tuiles([
        ("Ventes", fr(d["Global_Sales"].sum(), 0) + " M", f"{pct(part_v)} des ventes de la sélection"),
        ("Jeux", fr(len(d)), f"{pct(len(d) / len(df))} du catalogue"),
        ("Ventes par jeu", fr(d["Global_Sales"].mean(), 2) + " M", f"contre {fr(df['Global_Sales'].mean(), 2)} M tous genres"),
        ("Région la plus friande", NOMS_REG[aff.idxmax()], f"affinité ×{fr(aff.max(), 2)}"),
    ])
    gauche, droite = st.columns([1.4, 1])
    with gauche:
        st.markdown("**Titres les plus vendus**")
        t = D.titres(ctx["cle"])
        tableau_jeux(ctx, t[t["Genre"] == focus].head(10), key="g_top_titres")
    with droite:
        st.markdown("**Éditeurs dominants**")
        ed = d.groupby("Publisher")["Global_Sales"].sum().nlargest(8)
        graphique(G.barres_horizontales(ed, hauteur=330), key="g_editeurs")

    if D.persistant(st.toggle, "g_notes", "Afficher les notes Metacritic par genre"):
        _genres_notes(ctx, focus)


def _genres_notes(ctx: dict, focus: str) -> None:
    joint = D.joint(ctx["cle"])
    notes = joint[joint["Note_Presse"]]
    if len(notes) < 20:
        st.info("Trop peu de jeux notés dans la sélection : Metacritic couvre surtout les jeux sortis entre 2000 et 2016.")
        return
    g = notes.groupby("Genre", observed=True).agg(Jeux=("Name", "size"), Presse=("Critic_Score", "mean"),
                                                   Joueurs=("User_Score_100", "mean")).sort_values("Presse")
    st.markdown("**Note moyenne par genre : presse et joueurs**")
    graphique(G.notes_par_categorie(g, [C.GENRES_FR[x] for x in g.index], C.GENRES_FR[focus]), key="g_notes_graphe")
    d = notes[notes["Genre"] == focus]
    if len(d):
        st.caption(f"{C.GENRES_FR[focus]} : {fr(len(d))} jeux notés, note presse moyenne {fr(d['Critic_Score'].mean(), 1)}/100 "
                   f"(tous genres : {fr(notes['Critic_Score'].mean(), 1)}). Les jeux sans note Metacritic sont exclus.")


@st.fragment
def _genres_evolution(df: pd.DataFrame) -> None:
    genres = D.persistant(st.multiselect, "g_sel", "Genres à comparer", list(C.GENRES_FR), param="default",
                           format_func=C.GENRES_FR.get, max_selections=6)
    if not genres:
        st.info("Choisissez au moins un genre à comparer.")
        return
    v = df.pivot_table(index="Year", columns="Genre", values="Global_Sales", aggfunc="sum", observed=True).fillna(0)
    parts = v.div(v.sum(axis=1), axis=0).rolling(3, center=True, min_periods=1).mean()
    parts = parts.loc[parts.index >= 1985, [g for g in genres if g in parts.columns]]
    # 12 genres pour 8 couleurs : on colore les genres choisis dans l'ordre de sélection (6 au maximum)
    couleurs = {g: C.PALETTE[i] for i, g in enumerate(genres)}
    graphique(G.lignes(parts, couleurs, C.GENRES_FR, "Part des ventes de l'année"), key="g_lignes")
    st.caption("Moyenne mobile sur 3 ans. Six genres au maximum, pour que chaque courbe reste lisible.")


# --------------------------------------------------------------------------------------
# 4. Régions
# --------------------------------------------------------------------------------------

def vue_regions(ctx: dict) -> None:
    df = ctx["df"]
    entete("Régions et préférences culturelles", "Amérique du Nord, Europe, Japon : mêmes jeux, goûts différents ?")
    if garde_vide(df):
        return
    r = df[C.REGIONS].sum()
    tuiles([(NOMS_REG[k], fr(v, 0) + " M", f"{pct(v / r.sum())} des ventes") for k, v in r.items()])

    st.subheader("Poids des régions dans le temps")
    pr = df.groupby("Year")[C.REGIONS].sum()
    pr = pr.div(pr.sum(axis=1), axis=0).rolling(3, center=True, min_periods=1).mean()
    graphique(G.lignes(pr, C.COULEURS_REGION, NOMS_REG, "Part des ventes de l'année"), key="r_poids")

    st.subheader("Affinités genre-région")
    _regions_affinites(df)

    st.subheader("Les goûts régionaux convergent-ils ?")
    if (df["Year"] >= 1995).sum() == 0 or df.loc[df["Year"] >= 1995, "Year"].nunique() < 3:
        st.info("La convergence se mesure à partir de 1995 sur au moins trois années : élargissez la période pour l'afficher.")
    else:
        cv = I.convergence_regionale(df, annee_min=max(1995, int(df["Year"].min()))).rolling(3, center=True, min_periods=2).mean()
        noms = {"NA_Sales|EU_Sales": "Amérique du Nord - Europe", "NA_Sales|JP_Sales": "Amérique du Nord - Japon", "EU_Sales|JP_Sales": "Europe - Japon"}
        couleurs = dict(zip(noms, C.PALETTE[:3]))
        graphique(G.lignes(cv, couleurs, noms, "Divergence entre mix de genres", fmt=".3f"), key="r_conv")
        encart("L'Amérique du Nord et l'Europe achètent presque les mêmes genres (divergence ≈ 0,01). "
               "Le Japon s'en écarte nettement, et de plus en plus depuis 2012.")
    suite(ctx, "regions")


@st.fragment
def _regions_affinites(df: pd.DataFrame) -> None:
    mode = D.persistant(st.segmented_control, "r_mode", "Mesure", ["Affinité (préférences)", "Poids du genre dans la région"],
                        param="default", required=True, label_visibility="collapsed")
    if mode == "Poids du genre dans la région":
        v = df.groupby("Genre", observed=True)[C.REGIONS].sum()
        m = (v / v.sum()).sort_values("NA_Sales", ascending=False)
        graphique(G.heatmap_pct(m, [NOMS_REG[x] for x in C.REGIONS], [C.GENRES_FR[g] for g in m.index], "Part"), key="r_poids_g")
        st.caption("Chaque colonne fait 100 % : poids de chaque genre dans les ventes de la région.")
    else:
        a = I.affinite_genre_region(df)
        a = a.loc[a["JP_Sales"].sort_values(ascending=False).index]
        graphique(G.heatmap_pct(a, [NOMS_REG[x] for x in C.REGIONS], [C.GENRES_FR[g] for g in a.index], "Affinité",
                                diverging=True), key="r_aff")
        st.caption("Affinité = poids du genre dans la région / poids dans le monde. Rouge : sur-représenté ; bleu : sous-représenté.")


# --------------------------------------------------------------------------------------
# 5. Éditeurs et Market Power Index
# --------------------------------------------------------------------------------------

PREREGLAGES = {
    "Équilibré": {"part_marche": 20, "leadership": 20, "diversite": 20, "constance": 20, "taux_hits": 20},
    "Domination": {"part_marche": 45, "leadership": 40, "diversite": 5, "constance": 5, "taux_hits": 5},
    "Qualité": {"part_marche": 10, "leadership": 5, "diversite": 5, "constance": 20, "taux_hits": 60},
    "Polyvalence": {"part_marche": 10, "leadership": 5, "diversite": 50, "constance": 30, "taux_hits": 5},
}


def appliquer_prereglage() -> None:
    choix = st.session_state.get("mpi_preset")
    if choix:
        for k, v in PREREGLAGES[choix].items():
            D.definir(f"w_{k}", v)
    st.session_state["mpi_preset"] = None


def vue_mpi(ctx: dict) -> None:
    df = ctx["df"]
    entete("Éditeurs et Market Power Index", "Mesurer le pouvoir de marché au-delà de la taille, avec vos propres pondérations")
    if garde_vide(df):
        return

    with st.expander("Comment le MPI est-il calculé ?", expanded=False):
        st.markdown("""
| Composante | Calcul |
|---|---|
| Part de marché par genre | Part de l'éditeur dans chaque genre, pondérée par le poids du genre dans son catalogue |
| Leadership | Nombre de marchés *genre × année* (≥ 5 jeux) où l'éditeur dépasse 30 % des ventes |
| Diversité | Entropie de Shannon de ses ventes par genre, normalisée entre 0 et 1 |
| Constance régionale | 1 − CV(parts de marché NA, EU, JP, Autres) / √3 |
| Taux de succès | Part de ses titres dépassant 1 million d'exemplaires |
| *Qualité perçue (option)* | Note presse Metacritic moyenne, pondérée par les ventes, sur les notes d'au moins 5 critiques |

Chaque composante est ramenée entre 0 et 1, puis pondérée. Le score final va de 0 à 100.

La qualité perçue vient de la deuxième source (Metacritic). Quand moins de 30 % des jeux d'un éditeur sont notés,
sa note n'est pas représentative : on lui attribue la note médiane des éditeurs, qui ne le favorise ni ne le pénalise.
""")
    _mpi_corps(ctx)
    suite(ctx, "mpi")


@st.fragment
def _mpi_corps(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    df = ctx["df"]
    entete_poids, presets = st.columns([1, 2], vertical_alignment="center")
    entete_poids.markdown("**Pondérations**")
    presets.pills("Préréglages", list(PREREGLAGES), key="mpi_preset", on_change=appliquer_prereglage, label_visibility="collapsed")
    qualite = D.persistant(st.toggle, "mpi_qualite", "Inclure la qualité perçue (note presse Metacritic, 6e composante)")
    composantes = J.COMPOSANTES_QUALITE if qualite else I.COMPOSANTES
    cols = st.columns(len(composantes))
    poids = {k: D.persistant(cols[i].slider, f"w_{k}", label, 0, 100, step=5) for i, (k, label) in enumerate(composantes.items())}
    c1, c2, _ = st.columns([1, 1, 2])
    min_titres = D.persistant(c1.number_input, "mpi_min", "Titres minimum pour être classé", 5, 100, step=5)
    if qualite:
        normalisation = "minmax"
        c2.caption("<br>Normalisation min-max (celle du notebook de la deuxième base).", unsafe_allow_html=True)
    else:
        normalisation = D.persistant(c2.selectbox, "mpi_norm", "Normalisation", ["minmax", "rang"], param="index",
                                    format_func={"minmax": "Min-max", "rang": "Rangs (percentiles)"}.get)

    if sum(poids.values()) == 0:
        st.warning("Toutes les pondérations sont à zéro : donnez du poids à au moins une composante.")
        return
    try:
        if qualite:
            mpi = D.mpi_qualite(ctx["cle"], tuple(poids.items()), int(min_titres))
        else:
            mpi = D.mpi(ctx["cle"], tuple(poids.items()), int(min_titres), normalisation)
    except Exception:
        mpi = pd.DataFrame()
    if len(mpi) < 5:
        st.warning("Pas assez d'éditeurs éligibles avec ces filtres. Baissez le nombre minimum de titres ou élargissez la période.")
        return

    defaut = all(v == 20 for v in poids.values()) and min_titres == 20 and normalisation == "minmax" and not ctx["filtre_actif"]
    texte_defaut = " Paramètres du notebook bdd2_metacritic.ipynb (Partie V) : les résultats sont identiques." if qualite else \
        " Paramètres du notebook : les résultats sont identiques."
    st.caption(f"{len(mpi)} éditeurs classés." + (texte_defaut if defaut else "")
               + (f" Qualité non représentative (note médiane attribuée) pour {int((~mpi['qualite_representative']).sum())} éditeurs."
                  if qualite else ""))
    n_max = min(40, len(mpi))
    if n_max > 5:
        D.definir("mpi_n", min(D.valeur("mpi_n"), n_max))
        n = D.persistant(st.slider, "mpi_n", "Éditeurs affichés", 5, n_max)
    else:
        n = n_max
    if D.valeur("mpi_ed") not in mpi.index:
        D.definir("mpi_ed", mpi.index[0])

    def choisir_editeur(point: dict) -> None:
        D.definir("mpi_ed", point["y"])

    graphique(G.decomposition_mpi(mpi, poids, n, D.valeur("mpi_ed"), composantes), key="mpi_bar", clic=choisir_editeur)
    astuce("Cliquez sur un éditeur pour afficher sa fiche ci-dessous.")

    st.subheader("Fiche éditeur")
    s1, s2 = st.columns(2)
    editeur = D.persistant(s1.selectbox, "mpi_ed", "Éditeur", list(mpi.index), param="index")
    autres = ["(aucun)"] + [e for e in mpi.index if e != editeur]
    if D.valeur("mpi_cmp") not in autres:
        D.definir("mpi_cmp", "(aucun)")
    comparer = D.persistant(s2.selectbox, "mpi_cmp", "Comparer avec", autres, param="index")
    e = mpi.loc[editeur]
    tuiles([
        ("Rang MPI", f"{int(e['rang'])} / {len(mpi)}", "Selon vos pondérations"),
        ("MPI", fr(e["MPI"], 1), "Score de 0 à 100"),
        ("Ventes", fr(e["ventes"], 0) + " M", f"{pct(e['part_marche_globale'])} du marché"),
        ("Taux de hits", pct(e["taux_hits"], 0), f"{int(e['n_hits'])} titres sur {int(e['n_titres'])} au-delà de 1 M"),
        ("Genre principal", C.GENRES_FR.get(e["genre_principal"], e["genre_principal"]), "Genre qui génère le plus de ventes"),
    ])
    gauche, droite = st.columns([1, 1.15])
    with gauche:
        st.markdown(f"**Profil des {len(composantes)} composantes (scores normalisés)**")
        choisis = [editeur] + ([comparer] if comparer != "(aucun)" else [])
        graphique(G.radar_editeurs(mpi, choisis, G.COURTS_QUALITE if qualite else G.COURTS), key="mpi_radar")
    with droite:
        st.markdown(f"**Titres les plus vendus de {editeur}**")
        t = D.titres(ctx["cle"])
        tableau_jeux(ctx, t[t["Publisher"] == editeur].head(10), key="mpi_titres", hauteur=390)
    with st.expander("Valeurs détaillées des composantes"):
        comp = pd.DataFrame({
            "Composante": list(composantes.values()),
            "Valeur brute": [e[k] for k in composantes],
            "Score normalisé": [e[f"{k}_norm"] for k in composantes],
            "Médiane des éditeurs": [mpi[f"{k}_norm"].median() for k in composantes],
        })
        st.dataframe(comp, hide_index=True, column_config={
            "Valeur brute": st.column_config.NumberColumn(format="%.3f"),
            "Score normalisé": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
            "Médiane des éditeurs": st.column_config.NumberColumn(format="%.2f"),
        })

    st.subheader("Classement complet")
    classement = mpi[["rang", "MPI", "ventes", "part_marche", "genres_leader", "leadership", "diversite", "constance", "taux_hits",
                      *(["qualite"] if qualite else []), "n_titres", "genre_principal"]]
    affiche = classement.assign(genre_principal=classement["genre_principal"].map(C.GENRES_FR)).reset_index()

    def choisir_ligne(ligne: pd.Series) -> None:
        D.definir("mpi_ed", ligne["Publisher"])

    tableau(affiche, "mpi_classement", clic=choisir_ligne, hide_index=True, column_config={
        "Publisher": "Éditeur", "rang": "Rang",
        "MPI": st.column_config.ProgressColumn("MPI", min_value=0, max_value=100, format="%.1f"),
        "ventes": st.column_config.NumberColumn("Ventes (M)", format="%.0f"),
        "part_marche": st.column_config.NumberColumn("Part de marché / genre", format="percent"),
        "genres_leader": "Genres > 30 %", "leadership": "Marchés annuels dominés",
        "diversite": st.column_config.NumberColumn("Diversité", format="%.2f"),
        "constance": st.column_config.NumberColumn("Constance", format="%.2f"),
        "taux_hits": st.column_config.NumberColumn("Taux de hits", format="percent"),
        "qualite": st.column_config.NumberColumn("Qualité perçue", format="%.1f", help="Note presse moyenne pondérée par les ventes (/100)"),
        "n_titres": "Titres", "genre_principal": "Genre principal",
    })
    astuce("Cliquez sur une ligne pour afficher la fiche de cet éditeur plus haut.")
    st.download_button("Télécharger le classement (CSV)", classement.to_csv().encode("utf-8"), "bdd1_market_power_index.csv", "text/csv")


# --------------------------------------------------------------------------------------
# 6. Explorateur de jeux et divergences
# --------------------------------------------------------------------------------------

def vue_jeux(ctx: dict) -> None:
    df = ctx["df"]
    entete("Explorateur de jeux", "Profil régional d'un titre et outliers culturels")
    if garde_vide(df):
        return
    st.subheader("Profil régional d'un titre")
    _jeux_profil(ctx)

    st.subheader("Outliers culturels")
    _jeux_outliers(ctx)
    suite(ctx, "jeux")


@st.fragment
def _jeux_profil(ctx: dict) -> None:
    titres = D.titres(ctx["cle"])
    noms = titres["Name"].tolist()
    if D.valeur("jeu_nom") not in set(noms):
        D.definir("jeu_nom", noms[0])

    def au_hasard() -> None:
        succes = titres.loc[titres["Global_Sales"] >= 1, "Name"]
        D.definir("jeu_nom", (succes if len(succes) else titres["Name"]).sample(1).iloc[0])

    c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
    nom = D.persistant(c1.selectbox, "jeu_nom", "Rechercher un titre", noms, param="index",
                       help="Tapez quelques lettres pour filtrer. Les titres sont triés par ventes.")
    c2.button("🎲 Au hasard", on_click=au_hasard, width="stretch", help="Un titre vendu à plus d'un million d'exemplaires")
    profil_jeu(ctx, nom, prefixe="jeu")


@st.fragment
def _jeux_outliers(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    c1, c2 = st.columns([1, 2])
    min_ventes = D.persistant(c1.select_slider, "jeu_min", "Ventes minimales du titre", [0.3, 0.5, 1.0, 2.0],
                                format_func=lambda v: f"{fr(v, 1)} M")
    div = D.divergences(ctx["cle"], min_ventes)
    if len(div) < 10:
        st.warning("Trop peu de titres avec ces filtres.")
        return
    q1, q3 = div["divergence"].quantile([0.25, 0.75])
    seuil = q3 + 1.5 * (q3 - q1)
    c2.markdown(f"<br>{len(div)} titres analysés · seuil outlier (Q3 + 1,5 × IQR) = **{fr(seuil, 3)}** · "
                f"**{int(div['outlier'].sum())} outliers**", unsafe_allow_html=True)
    graphique(G.nuage_outliers(div, seuil), key="jeu_nuage", clic=lambda p: ouvrir_jeu(p["text"]) if p.get("text") else None)
    astuce("Survolez un point pour son profil, cliquez dessus pour ouvrir sa fiche. Cliquez dans la légende pour masquer une région.")

    region = D.persistant(st.pills, "jeu_reg", "Région sur-représentée", list(C.REGIONS), param="default",
                          format_func=NOMS_REG.get, required=True)
    o = div[div["outlier"] & (div["region_dominante"] == (region or "JP_Sales"))].nlargest(25, "Global_Sales").copy()
    parts_cols = ["part_NA_Sales", "part_EU_Sales", "part_JP_Sales", "part_Other_Sales"]
    o[parts_cols] = o[parts_cols] * 100
    o["Genre"] = o["Genre"].map(C.GENRES_FR)
    o = o[["Name", "Year", "Genre", "Publisher", "Global_Sales", *parts_cols, "divergence"]].reset_index(drop=True)
    tableau(o, "jeu_outliers", clic=lambda ligne: ouvrir_jeu(ligne["Name"]), hide_index=True, column_config={
        "Name": "Titre", "Year": st.column_config.NumberColumn("Année", format="%d"), "Publisher": "Éditeur",
        "Global_Sales": st.column_config.NumberColumn("Ventes (M)", format="%.2f"),
        "part_NA_Sales": st.column_config.NumberColumn("NA", format="%.0f %%"),
        "part_EU_Sales": st.column_config.NumberColumn("EU", format="%.0f %%"),
        "part_JP_Sales": st.column_config.NumberColumn("JP", format="%.0f %%"),
        "part_Other_Sales": st.column_config.NumberColumn("Autres", format="%.0f %%"),
        "divergence": st.column_config.ProgressColumn("Divergence", min_value=0, max_value=0.7, format="%.3f"),
    })


# --------------------------------------------------------------------------------------
# 7. Notes Metacritic (deuxième source)
# --------------------------------------------------------------------------------------

TRANCHES_NOTE = [0, 50, 60, 70, 80, 90, 101]
NOMS_TRANCHES = ["< 50", "50-59", "60-69", "70-79", "80-89", "90 et +"]


def jeux_notes(ctx: dict) -> pd.DataFrame:
    """Jeux de la sélection qui ont une note presse, avec leur tranche de note."""
    joint = D.joint(ctx["cle"])
    n = joint[joint["Note_Presse"]].copy()
    n["Tranche"] = pd.cut(n["Critic_Score"], TRANCHES_NOTE, right=False, labels=NOMS_TRANCHES)
    n["Hit"] = n["Global_Sales"] >= C.SEUIL_HIT
    return n


def vue_notes(ctx: dict) -> None:
    df = ctx["df"]
    entete("Notes Metacritic : la qualité perçue",
           "Deuxième source : notes de la presse et des joueurs, reliées aux ventes jeu par jeu")
    if garde_vide(df):
        return
    joint = D.joint(ctx["cle"])
    n = jeux_notes(ctx)
    ventes = joint["Global_Sales"].sum()
    deux = n.dropna(subset=["User_Score_100"])
    tuiles([
        ("Jeux reliés", pct(joint["Relie"].mean()), f"{fr(joint['Relie'].sum())} jeux sur {fr(len(joint))} retrouvés dans Metacritic"),
        ("Jeux notés", pct(len(n) / len(joint), 0),
         f"Ils font {pct(n['Global_Sales'].sum() / ventes, 0)} des ventes : les jeux notés sont les plus visibles"),
        ("Note presse moyenne", f"{fr(n['Critic_Score'].mean(), 1)}/100" if len(n) else "–", "Moyenne des jeux notés par la presse"),
        ("Note joueurs moyenne", f"{fr(deux['User_Score_100'].mean(), 1)}/100" if len(deux) else "–", "Note sur 10 ramenée sur 100"),
        ("Accord presse / joueurs", fr(deux["Critic_Score"].corr(deux["User_Score_100"]), 2) if len(deux) > 2 else "–",
         "Corrélation entre les deux notes (1 = parfaitement d'accord)"),
    ])
    if len(n) < 30:
        st.info("Trop peu de jeux notés dans la sélection : Metacritic couvre surtout les jeux sortis entre 2000 et 2016.")
        return
    encart("<b>Source</b> : <i>Video Game Sales with Ratings</i> (Kaggle), scraping de Metacritic du 22/12/2016, reliée aux ventes "
           "sur nom normalisé + plateforme + année. <b>Biais à garder en tête</b> : Metacritic note surtout les jeux récents et "
           "visibles. Les jeux les plus vendus ont deux fois plus de chances d'être notés que les moins vendus.")

    st.subheader("Une bonne note fait-elle vendre ?")
    _notes_ventes(ctx)

    st.subheader("Presse contre joueurs")
    _notes_presse_joueurs(ctx)

    st.subheader("Les régions réagissent-elles pareil aux notes ?")
    parts = n[C.REGIONS].div(n[C.REGIONS].sum(axis=1), axis=0)
    profil = parts.groupby(n["Tranche"], observed=True).mean()
    gauche, droite = st.columns([1.5, 1])
    with gauche:
        graphique(G.regions_par_note(profil), key="n_regions")
    with droite:
        correl = pd.Series({C.REGION_LABELS[r]: np.log10(n[r] + 0.01).corr(n["Critic_Score"]) for r in C.REGIONS})
        st.markdown("**Lien entre note et ventes, par région**")
        st.dataframe(correl.rename("Corrélation").to_frame(), column_config={
            "Corrélation": st.column_config.ProgressColumn(min_value=0, max_value=0.6, format="%.2f")})
        encart("Plus un jeu est mal noté, plus ses ventes sont concentrées en <b>Amérique du Nord</b>. L'<b>Europe</b> est le "
               "marché le plus sensible aux notes ; le <b>Japon</b> l'est le moins, car Metacritic regroupe des critiques occidentales.")
    suite(ctx, "notes")


@st.fragment
def _notes_ventes(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    n = jeux_notes(ctx)
    t = n.groupby("Tranche", observed=True).agg(Jeux=("Name", "size"), Ventes_medianes=("Global_Sales", "median"),
                                                 Taux_hits=("Hit", "mean"))
    tranches = [str(x) for x in t.index]
    if st.session_state.get("n_tranche") not in tranches:
        st.session_state["n_tranche"] = tranches[-1]
    focus = st.session_state["n_tranche"]

    def choisir_tranche(point: dict) -> None:
        st.session_state["n_tranche"] = str(point["x"])

    mesure = D.persistant(st.segmented_control, "n_mesure", "Mesure", ["Ventes médianes", "Taux de hits"], param="default",
                          required=True, label_visibility="collapsed")
    gauche, droite = st.columns([1.2, 1])
    with gauche:
        graphique(G.ventes_par_note(t, "Taux_hits" if mesure == "Taux de hits" else "Ventes_medianes", focus), key="n_ventes",
                  clic=choisir_tranche)
        astuce("Cliquez sur une tranche de note pour afficher ses meilleures ventes.")
    with droite:
        st.markdown(f"**Meilleures ventes parmi les jeux notés {focus}**")
        top = n[n["Tranche"].astype(str) == focus].nlargest(10, "Global_Sales")
        top = top[["Name", "Platform_Name", "Year", "Critic_Score", "Global_Sales"]].reset_index(drop=True)
        tableau(top, "n_top", clic=lambda ligne: ouvrir_jeu(ligne["Name"]), hide_index=True, height=390, column_config={
            "Name": "Titre", "Platform_Name": "Plateforme", "Year": st.column_config.NumberColumn("Année", format="%d"),
            "Critic_Score": st.column_config.NumberColumn("Presse", format="%.0f"),
            "Global_Sales": st.column_config.NumberColumn("Ventes (M)", format="%.2f"),
        })
    if {"< 50", "90 et +"} <= set(tranches):
        ratio = t.loc["90 et +", "Ventes_medianes"] / t.loc["< 50", "Ventes_medianes"]
        encart(f"Un jeu noté 90 et plus se vend en médiane <b>{fr(ratio, 0)} fois plus</b> qu'un jeu noté moins de 50 "
               f"({pct(t.loc['90 et +', 'Taux_hits'], 0)} de hits contre {pct(t.loc['< 50', 'Taux_hits'], 0)}). "
               "<b>Lien ne veut pas dire cause</b> : les jeux attendus ont à la fois plus de budget marketing, plus de critiques "
               "et de meilleures notes. Les jeux familiaux (<i>Wii Play</i>, <i>Kinect Adventures!</i>) se vendent par millions "
               "malgré des notes médiocres.")


@st.fragment
def _notes_presse_joueurs(ctx: dict) -> None:
    fiche_si_demandee(ctx)
    n = jeux_notes(ctx)
    gauche, droite = st.columns([1.2, 1])
    with gauche:
        par_an = n[n["Year"] >= 2000].groupby("Year")[["Critic_Score", "User_Score_100"]].mean()
        if len(par_an) >= 3:
            st.markdown("**Note moyenne par année de sortie**")
            graphique(G.notes_par_annee(par_an), key="n_annees")
            st.caption("Depuis 2000 (avant, trop peu de jeux notés). Vers 2010, les joueurs deviennent plus sévères que la presse.")
        else:
            st.info("Élargissez la période (2000-2016) pour comparer l'évolution des deux notes.")
    with droite:
        sens = D.persistant(st.segmented_control, "n_sens", "Écart", ["Presse plus enthousiaste", "Joueurs plus enthousiastes"],
                            param="default", required=True, label_visibility="collapsed")
        fiables = n[n["Note_Presse_Fiable"].astype(bool) & n["Note_Joueurs_Fiable"].astype(bool)]
        ecarts = fiables.sort_values("Ecart_Presse_Joueurs", ascending=sens == "Joueurs plus enthousiastes").head(10)
        ecarts = ecarts[["Name", "Platform_Name", "Year", "Critic_Score", "User_Score_100", "User_Count"]].reset_index(drop=True)
        tableau(ecarts, "n_ecarts", clic=lambda ligne: ouvrir_jeu(ligne["Name"]), hide_index=True, height=390, column_config={
            "Name": "Titre", "Platform_Name": "Plateforme", "Year": st.column_config.NumberColumn("Année", format="%d"),
            "Critic_Score": st.column_config.NumberColumn("Presse", format="%.0f"),
            "User_Score_100": st.column_config.NumberColumn("Joueurs", format="%.0f"),
            "User_Count": st.column_config.NumberColumn("Votes", format="%d"),
        })
        st.caption("Notes fiables uniquement (au moins 5 critiques et 10 votes). Cliquez sur une ligne pour la fiche du jeu.")


# --------------------------------------------------------------------------------------
# 8. Qualité des données
# --------------------------------------------------------------------------------------

def vue_qualite(ctx: dict) -> None:
    raw, df_all, journal = ctx["raw"], ctx["df_all"], ctx["journal"]
    entete("Qualité des données", "Du fichier brut au jeu d'analyse : chaque correction est tracée")
    onglet_ventes, onglet_notes = st.tabs(["Ventes (bdd1_vgsales.csv)", "Notes (Metacritic)"])
    with onglet_ventes:
        tuiles([
            ("Lignes brutes", fr(len(raw)), "bdd1_vgsales.csv"),
            ("Jeux propres", fr(len(df_all)), "Après nettoyage"),
            ("Volume conservé", pct(df_all["Global_Sales"].sum() / raw["Global_Sales"].sum()), "Part des ventes du fichier brut"),
            ("Valeurs manquantes", "0", f"contre {int(raw.isna().sum().sum())} dans le brut"),
        ])
        st.subheader("Journal de nettoyage")
        st.dataframe(pd.DataFrame(journal), hide_index=True, column_config={"Détail": st.column_config.TextColumn(width="large")})

        st.subheader("Les problèmes trouvés dans le fichier brut")
        encart("""
        <ul>
        <li><b>271 années manquantes</b> : 118 retrouvées grâce à une fiche jumelle ou aux autres plateformes du même titre, 153 supprimées (0,5 % des ventes).</li>
        <li><b>261 éditeurs inconnus</b> sous deux libellés (vide et « Unknown ») : regroupés sous « Inconnu ».</li>
        <li><b>149 fiches partielles</b> « (JP sales) », « (US sales) »... : fusionnées dans la fiche principale en prenant le maximum par région, pour ne jamais compter deux fois les mêmes ventes.</li>
        <li><b>Doublons d'écriture</b> (« wwe Smackdown » / « WWE SmackDown! ») détectés grâce à une clé de nom normalisée.</li>
        <li><b>Dates impossibles</b> : 4 sorties après 2016, un jeu DS daté de 1985.</li>
        <li><b>Limites non corrigeables</b> : 2016 incomplète, ventes dématérialisées absentes, quelques ventes européennes saisies en « reste du monde » (Gran Turismo 4).</li>
        </ul>
        """)
        st.subheader("Données nettoyées")
        _qualite_apercu(df_all)
        st.download_button("Télécharger le jeu nettoyé (CSV)", df_all.to_csv(index=False).encode("utf-8"), "bdd1_vgsales_clean.csv", "text/csv")
    with onglet_notes:
        _qualite_notes()
    suite(ctx, "qualite")


def _qualite_notes() -> None:
    raw2, notes, journal2 = D.charger_notes()
    bilan = J.bilan_jointure(D.joint_complet(), notes)
    tuiles([
        ("Lignes brutes", fr(len(raw2)), "bdd2_metacritic.csv (Kaggle, scraping Metacritic du 22/12/2016)"),
        ("Jeux propres", fr(len(notes)), "Après nettoyage, une ligne par jeu et par plateforme"),
        ("Notes presse", fr(notes["Critic_Score"].notna().sum()), f"{pct(notes['Critic_Score'].notna().mean(), 0)} des jeux : non imputées"),
        ("Jeux reliés aux ventes", pct(bilan.loc["reliés à la base Metacritic", "Part des jeux"]),
         f"{pct(bilan.loc['reliés à la base Metacritic', 'Part des ventes'], 2)} des ventes"),
    ])
    st.subheader("Journal de nettoyage de la deuxième base")
    st.dataframe(pd.DataFrame(journal2), hide_index=True, column_config={"Détail": st.column_config.TextColumn(width="large")})

    st.subheader("Jointure avec les ventes")
    st.dataframe(bilan, column_config={
        "Jeux": st.column_config.NumberColumn(format="%d"), "Ventes (M)": st.column_config.NumberColumn(format="%.1f"),
        "Part des jeux": st.column_config.NumberColumn(format="percent"),
        "Part des ventes": st.column_config.NumberColumn(format="percent"),
    })
    encart("""
    <ul>
    <li><b>Clé de jointure</b> : nom normalisé (minuscules, sans ponctuation ni suffixe « (JP sales) ») + plateforme + année. L'année sépare un jeu de son remake.</li>
    <li><b>2 425 notes joueurs « tbd »</b> (pas assez de votes) : remplacées par des valeurs manquantes, la colonne devient numérique.</li>
    <li><b>Notes manquantes non imputées</b> : elles ne manquent pas au hasard (1 % de jeux notés dans les années 80, 61 % dans les années 2000).</li>
    <li><b>Fausses correspondances de la source</b> : <i>Need for Speed: Most Wanted</i> 2005 et son remake de 2012 avaient la même note. Note retirée plutôt qu'attribuée au hasard.</li>
    <li><b>Deux relevés de ventes différents</b> (<i>Wii Sports</i> : 82,74 M contre 82,53 M) : les ventes viennent toujours de bdd1_vgsales.csv, la seule source de vérité.</li>
    </ul>
    """)
    st.download_button("Télécharger les notes nettoyées (CSV)", notes.to_csv(index=False).encode("utf-8"),
                       "bdd2_metacritic_clean.csv", "text/csv")


@st.fragment
def _qualite_apercu(df_all: pd.DataFrame) -> None:
    recherche = D.persistant(st.text_input, "q_recherche", "Rechercher", placeholder="Titre, plateforme ou éditeur (ex. Zelda, PS2, Capcom)",
                              label_visibility="collapsed")
    d = df_all
    if recherche:
        r = recherche.strip()
        d = d[d["Name"].str.contains(r, case=False, regex=False) | d["Publisher"].str.contains(r, case=False, regex=False)
              | d["Platform"].astype(str).str.fullmatch(r, case=False) | d["Platform_Name"].astype(str).str.contains(r, case=False, regex=False)]
        st.caption(f"{fr(len(d))} jeux trouvés" + (" (500 premiers affichés)" if len(d) > 500 else ""))
    else:
        st.caption(f"500 premiers jeux sur {fr(len(df_all))}. Tapez un mot-clé pour chercher dans tout le jeu nettoyé.")
    st.dataframe(d.head(500), hide_index=True, column_config={"Year": st.column_config.NumberColumn(format="%d")})


# --------------------------------------------------------------------------------------
# 9. Synthèse et conclusion
# --------------------------------------------------------------------------------------

def _num(prefixe: str, debut: int, fin: int) -> list[str]:
    return [f"{prefixe}_{i:02d}" for i in range(debut, fin + 1)]


GALERIE = {
    "I. Nettoyage": _num("bdd1", 1, 1),
    "II. Analyse exploratoire": _num("bdd1", 2, 12),
    "II. Indicateurs avancés": _num("bdd1", 13, 19),
    "III. Storytelling": _num("bdd1", 20, 24),
    "IV. Notes Metacritic": _num("bdd2", 1, 10),
    "V. Jointure": _num("bdd2", 11, 14),
}


def carte(chiffre: str, titre: str, texte: str) -> str:
    return (f"<div class='carte'><div class='carte-chiffre'>{chiffre}</div>"
            f"<div class='carte-titre'>{titre}</div><div class='carte-texte'>{texte}</div></div>")


@st.cache_data(show_spinner=False)
def _insights() -> dict:
    df = D.filtrer(D.CLE_COMPLETE)
    s = df["Global_Sales"].sort_values(ascending=False).to_numpy()
    annuel = df.groupby("Year")["Global_Sales"].sum()
    pic = int(annuel.loc[: C.ANNEE_MAX - 1].idxmax())
    d = df.assign(Periode=I.periode(df["Year"]))
    v = d.groupby(["Periode", "Genre"], observed=True)["Global_Sales"].sum().unstack("Genre")
    parts = v.div(v.sum(axis=1), axis=0)
    div = D.divergences(D.CLE_COMPLETE, 0.5)
    mpi = I.market_power_index(df)
    return {
        "top10_pct": s[: int(0.10 * len(s))].sum() / s.sum(), "mediane": df["Global_Sales"].median(),
        "pic": pic, "ventes_pic": annuel[pic],
        "constr": df.groupby("Manufacturer", observed=True)["Global_Sales"].sum() / s.sum(),
        "ps2": df.loc[df["Platform"] == "PS2", "Global_Sales"].sum(),
        "act_tir_avant": parts.loc["1995-1999", ["Action", "Shooter"]].sum(),
        "act_tir_apres": parts.loc["2010-2016", ["Action", "Shooter"]].sum(),
        "aff": I.affinite_genre_region(df),
        "part_jp_outliers": (div.loc[div["outlier"], "region_dominante"] == "JP_Sales").mean(),
        "mpi_nintendo": mpi.loc["Nintendo", "MPI"], "mpi_2": (mpi.index[1], mpi["MPI"].iloc[1]),
    }


@st.cache_data(show_spinner=False)
def _insights_notes() -> dict:
    joint = D.joint(D.CLE_COMPLETE)
    n = joint[joint["Note_Presse"]]
    tranche = pd.cut(n["Critic_Score"], TRANCHES_NOTE, right=False, labels=NOMS_TRANCHES)
    mediane = n.groupby(tranche, observed=True)["Global_Sales"].median()
    parts_na = (n["NA_Sales"] / n[C.REGIONS].sum(axis=1)).groupby(tranche, observed=True).mean()
    avant = I.market_power_index(D.filtrer(D.CLE_COMPLETE))["rang"]
    apres = J.market_power_index_qualite(joint)
    gain = (avant - apres["rang"]).loc[apres.index[:12]]
    return {
        "ratio": mediane["90 et +"] / mediane["< 50"], "hits": n.groupby(tranche, observed=True)["Global_Sales"].apply(
            lambda s: (s >= C.SEUIL_HIT).mean()),
        "podium": list(apres.index[:3]), "montent": list(gain.nlargest(2).index), "descendent": list(gain.nsmallest(2).index),
        "na_bas": parts_na["< 50"], "na_haut": parts_na["90 et +"],
    }


def vue_conclusion(ctx: dict) -> None:
    entete("Synthèse et conclusion", "Les résultats du projet en un coup d'œil, calculés sur l'ensemble du jeu nettoyé (1980-2016)")

    # Tous les chiffres sont recalculés ici : ils restent cohérents avec le notebook si les données changent.
    x = _insights()
    aff, constr = x["aff"], x["constr"]
    cartes = [
        (pct(x["top10_pct"], 0), "Un marché de blockbusters",
         f"des ventes réalisées par 10 % des jeux. La médiane d'un jeu n'est que de {fr(x['mediane'], 2)} M d'exemplaires.", "accueil"),
        (f"{fr(x['ventes_pic'], 0)} M", f"Un pic en {x['pic']}",
         "puis un recul du physique : le dématérialisé et le mobile, absents de la source, prennent le relais.", "tendances"),
        (pct(constr["Sony"] + constr["Nintendo"], 0), "Le duopole Sony-Nintendo",
         f"des ventes de jeux sur leurs consoles. La PS2 reste la plateforme record ({fr(x['ps2'], 0)} M de jeux).", "tendances"),
        (f"{pct(x['act_tir_avant'], 0)} → {pct(x['act_tir_apres'], 0)}", "L'Action et le Tir prennent le pouvoir",
         "part des ventes mondiales entre 1995-1999 et 2010-2016, au détriment des Plates-formes et de la Course.", "genres"),
        (f"×{fr(aff.loc['Role-Playing', 'JP_Sales'], 1)}", "Le Japon, un marché à part",
         f"d'affinité pour le RPG, ×{fr(aff.loc['Shooter', 'JP_Sales'], 2)} pour le Tir ; "
         f"{pct(x['part_jp_outliers'], 0)} des outliers culturels sont japonais.", "regions"),
        (f"{fr(x['mpi_nintendo'], 1)}/100", "Nintendo, hors catégorie",
         f"au Market Power Index, devant {x['mpi_2'][0]} ({fr(x['mpi_2'][1], 1)}). "
         "Le pouvoir de marché récompense le taux de succès plus que la taille.", "mpi"),
    ]
    st.subheader("Six insights clés")
    for ligne in (cartes[:3], cartes[3:]):
        for col, (chiffre, titre, texte, page) in zip(st.columns(3), ligne):
            col.markdown(carte(chiffre, titre, texte), unsafe_allow_html=True)
            col.page_link(ctx["pages"][page], label="Explorer →")

    y = _insights_notes()
    cartes_notes = [
        (f"×{fr(y['ratio'], 0)}", "Une bonne note va avec de bonnes ventes",
         f"de ventes médianes pour un jeu noté 90 et plus face à un jeu noté moins de 50 ({pct(y['hits']['90 et +'], 0)} de hits "
         f"contre {pct(y['hits']['< 50'], 0)}). Un lien, pas forcément une cause : le budget marketing joue sur les deux.", "notes"),
        ("Top 3 inchangé", "La qualité reclasse les éditeurs",
         f"{', '.join(y['podium'])} gardent le podium du MPI, mais les éditeurs premium montent ({', '.join(y['montent'])}) et les éditeurs de volume "
         f"descendent ({', '.join(y['descendent'])}).", "mpi"),
        (f"{pct(y['na_bas'], 0)} → {pct(y['na_haut'], 0)}", "Les jeux mal notés se vendent en Amérique du Nord",
         "part nord-américaine des ventes d'un jeu noté moins de 50, puis 90 et plus. L'Europe est la plus sensible aux notes, "
         "le Japon la moins.", "notes"),
    ]
    st.subheader("Ce qu'apporte la deuxième source (notes Metacritic)")
    for col, (chiffre, titre, texte, page) in zip(st.columns(3), cartes_notes):
        col.markdown(carte(chiffre, titre, texte), unsafe_allow_html=True)
        col.page_link(ctx["pages"][page], label="Explorer →")

    gauche, droite = st.columns(2)
    with gauche:
        st.subheader("Difficultés de data wrangling")
        encart("""
        <ul>
        <li><b>Des problèmes invisibles</b> pour <code>isna()</code> et <code>duplicated()</code> : 149 fiches partielles « (JP sales) », doublons d'écriture, un jeu DS daté de 1985.</li>
        <li><b>Des étapes imbriquées</b> : une clé de jeu normalisée a été nécessaire pour imputer les années, puis fusionner les fiches.</li>
        <li><b>Fusionner sans double compter</b> : maximum par région plutôt que somme (<i>Ratchet &amp; Clank</i>).</li>
        <li><b>Des limites de la source</b> signalées plutôt que masquées : 2016 incomplète, dématérialisé absent, ventes européennes saisies en « reste du monde ».</li>
        <li><b>Relier deux sources</b> : notes « tbd », remakes notés comme l'original, deux relevés de ventes différents, et des notes qui ne couvrent que les jeux récents et visibles.</li>
        </ul>
        """)
    with droite:
        st.subheader("Apport des visualisations")
        encart("""
        <ul>
        <li><b>Révéler</b> : la courbe de concentration et la carte des cycles de vie rendent les structures du marché évidentes.</li>
        <li><b>Comparer à la bonne échelle</b> : l'indice d'affinité, en échelle logarithmique, neutralise la taille des régions.</li>
        <li><b>Éviter les faux messages</b> : pas de double axe, 2016 grisée, une couleur fixe par constructeur et par région.</li>
        <li><b>Qualifier la confiance</b> : le test de robustesse du MPI montre ce qui est solide (top 4) et ce qui dépend des hypothèses.</li>
        </ul>
        """)

    st.subheader("Galerie des figures du notebook")
    st.caption("Les graphiques interprétés des notebooks (bdd1_vgsales.ipynb et bdd2_metacritic.ipynb), exportés en PNG dans le dossier figures/. "
               "Survolez une figure et cliquez sur l'icône plein écran pour l'agrandir.")
    _galerie()


@st.fragment
def _galerie() -> None:
    # Une seule partie affichée à la fois (et non des onglets) : la page ne charge que les images regardées.
    fichiers = {f.stem[:7]: f for f in sorted(C.FIGURES_DIR.glob("bdd[12]_*.png"))}
    if not fichiers:
        st.info("Aucune figure trouvée : exécutez le notebook pour les générer dans figures/.")
        return
    partie = D.persistant(st.segmented_control, "c_galerie", "Partie", list(GALERIE), param="default", required=True,
                                  label_visibility="collapsed")
    presentes = [fichiers[n] for n in GALERIE[partie] if n in fichiers]
    for i in range(0, len(presentes), 2):
        for col, f in zip(st.columns(2), presentes[i:i + 2]):
            legende = f.stem[8:].replace("_", " ").replace("story ", "").replace("jointure ", "").capitalize()
            col.image(str(f), caption=f"BDD {f.stem[3]} · figure {f.stem[5:7]} · {legende}", width="stretch")
