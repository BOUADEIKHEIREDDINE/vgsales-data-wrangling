"""Pages de l'interface. Chaque page reçoit le contexte : données filtrées, données complètes, journal."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from modules import config as C
from modules import indicators as I

from . import charts as G

NOMS_REG = C.REGION_LABELS


def fr(v: float, d: int = 0) -> str:
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def pct(v: float, d: int = 1) -> str:
    return f"{fr(v * 100, d)} %"


def entete(titre: str, sous_titre: str) -> None:
    st.markdown(f"<h1 class='titre'>{titre}</h1><p class='sous-titre'>{sous_titre}</p>", unsafe_allow_html=True)


def encart(texte: str) -> None:
    st.markdown(f"<div class='encart'>{texte}</div>", unsafe_allow_html=True)


def tuiles(valeurs: list[tuple[str, str, str]]) -> None:
    for col, (label, valeur, aide) in zip(st.columns(len(valeurs)), valeurs):
        col.metric(label, valeur, help=aide, border=True)


def garde_vide(df: pd.DataFrame) -> bool:
    if df.empty:
        st.warning("Aucun jeu ne correspond aux filtres choisis. Élargissez la période ou les sélections dans la barre latérale.")
        return True
    return False


# --------------------------------------------------------------------------------------
# 1. Vue d'ensemble
# --------------------------------------------------------------------------------------

def vue_ensemble(ctx: dict) -> None:
    df = ctx["df"]
    debut, fin = int(df["Year"].min()) if len(df) else 1980, int(df["Year"].max()) if len(df) else 2016
    entete(f"Le marché mondial du jeu vidéo, {debut}-{fin}",
           f"Ventes physiques de {fr(len(df))} jeux nettoyés · source VGChartz · millions d'exemplaires")
    if garde_vide(df):
        return
    total = df["Global_Sales"].sum()
    titres = I.titres(df)
    top10 = df.groupby("Publisher")["Global_Sales"].sum().nlargest(10).sum() / total
    tuiles([
        ("Ventes", fr(total, 0) + " M", "Exemplaires vendus, toutes régions"),
        ("Jeux", fr(len(df)), "Couples titre / plateforme"),
        ("Titres", fr(len(titres)), "Titres distincts, toutes plateformes"),
        ("Éditeurs", fr(df["Publisher"].nunique()), "Dont la modalité « Inconnu »"),
        ("Part du top 10 éditeurs", pct(top10, 0), "Concentration du marché de l'édition"),
    ])

    st.subheader("Un marché porté par les cycles de consoles")
    en_part = st.segmented_control("Affichage", ["Volume", "Part de marché"], default="Volume", key="ens_part",
                                   label_visibility="collapsed") == "Part de marché"
    st.plotly_chart(G.ventes_par_constructeur(df, en_part), key="ens_constructeurs")

    gauche, droite = st.columns([1.15, 1])
    with gauche:
        st.subheader("Top 10 des titres")
        t = titres.nlargest(10, "Global_Sales")
        couleurs = [C.PALETTE[7] if p == "Nintendo" else C.GRIS for p in t["Publisher"]]
        st.plotly_chart(G.barres_horizontales(t.set_index("Name")["Global_Sales"], couleurs, hauteur=420), key="ens_top")
        st.caption("Rouge : Nintendo. Les ventes d'un titre additionnent toutes ses plateformes.")
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


# --------------------------------------------------------------------------------------
# 2. Tendances et plateformes
# --------------------------------------------------------------------------------------

def vue_tendances(ctx: dict) -> None:
    df = ctx["df"]
    entete("Tendances et plateformes", "Combien de jeux, combien de ventes, et sur quelles consoles")
    if garde_vide(df):
        return
    annuel = df.groupby("Year").agg(jeux=("Name", "size"), ventes=("Global_Sales", "sum"))
    annuel["par_jeu"] = annuel["ventes"] / annuel["jeux"]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Jeux sortis par année**")
        st.plotly_chart(G.barres_annuelles(annuel["jeux"], "Nombre de jeux", "%{y:,} jeux"), key="t_jeux")
    with c2:
        st.markdown("**Ventes mondiales par année de sortie**")
        st.plotly_chart(G.barres_annuelles(annuel["ventes"], "Ventes (M)", "%{y:,.0f} M"), key="t_ventes")
    st.markdown("**Ventes moyennes par jeu**")
    st.plotly_chart(G.barres_annuelles(annuel["par_jeu"], "M par jeu", "%{y:.2f} M par jeu"), key="t_moy")
    encart("Après 2011, il sort deux fois moins de jeux mais chacun vend davantage : les éditeurs concentrent leurs budgets "
           "sur quelques franchises. En gris : 2016, année incomplète dans la source.")

    st.subheader("Cycle de vie des plateformes")
    n = st.slider("Nombre de plateformes", 8, 31, 20, key="t_n")
    st.plotly_chart(G.cycle_de_vie(df, n), key="t_cycle")

    st.subheader("Classement des plateformes")
    p = df.groupby("Platform", observed=True).agg(
        Plateforme=("Platform_Name", "first"), Constructeur=("Manufacturer", "first"), Type=("Platform_Type", "first"),
        Jeux=("Name", "size"), Ventes=("Global_Sales", "sum"), Début=("Year", "min"), Fin=("Year", "max"),
    ).sort_values("Ventes", ascending=False)
    p["Part"] = p["Ventes"] / p["Ventes"].sum()
    p["Ventes par jeu"] = p["Ventes"] / p["Jeux"]
    st.dataframe(p, hide_index=True, column_config={
        "Ventes": st.column_config.ProgressColumn("Ventes (M)", format="%.0f", min_value=0, max_value=float(p["Ventes"].max())),
        "Part": st.column_config.NumberColumn(format="percent"),
        "Ventes par jeu": st.column_config.NumberColumn(format="%.2f M"),
        "Début": st.column_config.NumberColumn(format="%d"), "Fin": st.column_config.NumberColumn(format="%d"),
    })


# --------------------------------------------------------------------------------------
# 3. Genres
# --------------------------------------------------------------------------------------

def vue_genres(ctx: dict) -> None:
    df = ctx["df"]
    entete("Genres", "Ce qui est produit, ce qui se vend, et comment cela évolue")
    if garde_vide(df):
        return
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**Fréquence et ventes : quels genres sur-performent ?**")
        st.plotly_chart(G.frequence_vs_ventes(df), key="g_scatter")
        st.caption("Au-dessus de la diagonale, le genre vend plus que son poids dans le catalogue.")
    with c2:
        st.markdown("**Ventes mondiales par genre**")
        v = df.groupby("Genre", observed=True)["Global_Sales"].sum().sort_values(ascending=False)
        v.index = [C.GENRES_FR[g] for g in v.index]
        st.plotly_chart(G.barres_horizontales(v, hauteur=430), key="g_barres")

    st.subheader("Évolution de la part des genres")
    genres = st.multiselect("Genres à comparer", list(C.GENRES_FR), default=["Action", "Shooter", "Platform", "Role-Playing"],
                            format_func=C.GENRES_FR.get, max_selections=6, key="g_sel")
    if genres:
        v = df.pivot_table(index="Year", columns="Genre", values="Global_Sales", aggfunc="sum", observed=True).fillna(0)
        parts = v.div(v.sum(axis=1), axis=0).rolling(3, center=True, min_periods=1).mean()
        parts = parts.loc[parts.index >= 1985, [g for g in genres if g in parts.columns]]
        # 12 genres pour 8 couleurs : on colore les genres choisis dans l'ordre de sélection (6 au maximum)
        couleurs = {g: C.PALETTE[i] for i, g in enumerate(genres)}
        st.plotly_chart(G.lignes(parts, couleurs, C.GENRES_FR, "Part des ventes de l'année"), key="g_lignes")
        st.caption("Moyenne mobile sur 3 ans. Six genres au maximum, pour que chaque courbe reste lisible.")

    st.subheader("Qui domine chaque genre ?")
    pg = I.parts_genre(df[df["Publisher"] != "Inconnu"])
    leaders = pd.DataFrame({
        "Genre": [C.GENRES_FR[g] for g in pg.columns], "Leader": pg.idxmax().to_numpy(), "Part du leader": pg.max().to_numpy(),
        "N°2": pg.apply(lambda c: c.nlargest(2).index[1]).to_numpy(), "Part du n°2": pg.apply(lambda c: c.nlargest(2).iloc[1]).to_numpy(),
    }).sort_values("Part du leader", ascending=False)
    leaders[["Part du leader", "Part du n°2"]] *= 100
    st.dataframe(leaders, hide_index=True, column_config={
        "Part du leader": st.column_config.ProgressColumn(format="%.0f %%", min_value=0, max_value=100),
        "Part du n°2": st.column_config.NumberColumn(format="%.0f %%"),
    })


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
    st.plotly_chart(G.lignes(pr, C.COULEURS_REGION, NOMS_REG, "Part des ventes de l'année"), key="r_poids")

    st.subheader("Affinités genre-région")
    mode = st.segmented_control("Mesure", ["Affinité (préférences)", "Poids du genre dans la région"],
                                default="Affinité (préférences)", key="r_mode", label_visibility="collapsed")
    if mode == "Poids du genre dans la région":
        v = df.groupby("Genre", observed=True)[C.REGIONS].sum()
        m = (v / v.sum()).sort_values("NA_Sales", ascending=False)
        st.plotly_chart(G.heatmap_pct(m, [NOMS_REG[x] for x in C.REGIONS], [C.GENRES_FR[g] for g in m.index], "Part"), key="r_poids_g")
        st.caption("Chaque colonne fait 100 % : poids de chaque genre dans les ventes de la région.")
    else:
        a = I.affinite_genre_region(df)
        a = a.loc[a["JP_Sales"].sort_values(ascending=False).index]
        st.plotly_chart(G.heatmap_pct(a, [NOMS_REG[x] for x in C.REGIONS], [C.GENRES_FR[g] for g in a.index], "Affinité",
                                      diverging=True), key="r_aff")
        st.caption("Affinité = poids du genre dans la région / poids dans le monde. Rouge : sur-représenté ; bleu : sous-représenté.")

    st.subheader("Les goûts régionaux convergent-ils ?")
    if (df["Year"] >= 1995).sum() == 0 or df.loc[df["Year"] >= 1995, "Year"].nunique() < 3:
        st.info("La convergence se mesure à partir de 1995 sur au moins trois années : élargissez la période pour l'afficher.")
        return
    cv = I.convergence_regionale(df, annee_min=max(1995, int(df["Year"].min()))).rolling(3, center=True, min_periods=2).mean()
    noms = {"NA_Sales|EU_Sales": "Amérique du Nord - Europe", "NA_Sales|JP_Sales": "Amérique du Nord - Japon", "EU_Sales|JP_Sales": "Europe - Japon"}
    couleurs = dict(zip(noms, C.PALETTE[:3]))
    st.plotly_chart(G.lignes(cv, couleurs, noms, "Divergence entre mix de genres", fmt=".3f"), key="r_conv")
    encart("L'Amérique du Nord et l'Europe achètent presque les mêmes genres (divergence ≈ 0,01). "
           "Le Japon s'en écarte nettement, et de plus en plus depuis 2012.")


# --------------------------------------------------------------------------------------
# 5. Éditeurs et Market Power Index
# --------------------------------------------------------------------------------------

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

Chaque composante est ramenée entre 0 et 1, puis pondérée. Le score final va de 0 à 100.
""")

    st.markdown("**Pondérations**")
    cols = st.columns(5)
    poids = {k: cols[i].slider(label, 0, 100, 20, 5, key=f"w_{k}") for i, (k, label) in enumerate(I.COMPOSANTES.items())}
    c1, c2, _ = st.columns([1, 1, 2])
    min_titres = c1.number_input("Titres minimum pour être classé", 5, 100, 20, 5, key="mpi_min")
    normalisation = c2.selectbox("Normalisation", ["minmax", "rang"], format_func={"minmax": "Min-max", "rang": "Rangs (percentiles)"}.get, key="mpi_norm")

    if sum(poids.values()) == 0:
        st.warning("Toutes les pondérations sont à zéro : donnez du poids à au moins une composante.")
        return
    try:
        mpi = I.market_power_index(df, poids=poids, min_titres=int(min_titres), normalisation=normalisation)
    except Exception:
        mpi = pd.DataFrame()
    if len(mpi) < 5:
        st.warning("Pas assez d'éditeurs éligibles avec ces filtres. Baissez le nombre minimum de titres ou élargissez la période.")
        return

    defaut = all(v == 20 for v in poids.values()) and min_titres == 20 and normalisation == "minmax" and ctx["filtre_actif"] is False
    st.caption(f"{len(mpi)} éditeurs classés." + (" Paramètres du notebook : les résultats sont identiques." if defaut else ""))
    n = st.slider("Éditeurs affichés", 5, min(40, len(mpi)), min(15, len(mpi)), key="mpi_n")
    st.plotly_chart(G.decomposition_mpi(mpi, poids, n), key="mpi_bar")

    st.subheader("Fiche éditeur")
    editeur = st.selectbox("Éditeur", mpi.index, key="mpi_ed")
    e = mpi.loc[editeur]
    tuiles([
        ("Rang MPI", f"{int(e['rang'])} / {len(mpi)}", "Selon vos pondérations"),
        ("MPI", fr(e["MPI"], 1), "Score de 0 à 100"),
        ("Ventes", fr(e["ventes"], 0) + " M", f"{pct(e['part_marche_globale'])} du marché"),
        ("Taux de hits", pct(e["taux_hits"], 0), f"{int(e['n_hits'])} titres sur {int(e['n_titres'])} au-delà de 1 M"),
        ("Genre principal", C.GENRES_FR.get(e["genre_principal"], e["genre_principal"]), "Genre qui génère le plus de ventes"),
    ])
    comp = pd.DataFrame({
        "Composante": list(I.COMPOSANTES.values()),
        "Valeur brute": [e["part_marche"], e["leadership"], e["diversite"], e["constance"], e["taux_hits"]],
        "Score normalisé": [e[f"{k}_norm"] for k in I.COMPOSANTES],
        "Médiane des éditeurs": [mpi[f"{k}_norm"].median() for k in I.COMPOSANTES],
    })
    st.dataframe(comp, hide_index=True, column_config={
        "Valeur brute": st.column_config.NumberColumn(format="%.3f"),
        "Score normalisé": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
        "Médiane des éditeurs": st.column_config.NumberColumn(format="%.2f"),
    })

    st.subheader("Classement complet")
    tableau = mpi[["rang", "MPI", "ventes", "part_marche", "genres_leader", "leadership", "diversite", "constance", "taux_hits", "n_titres", "genre_principal"]]
    st.dataframe(tableau.assign(genre_principal=tableau["genre_principal"].map(C.GENRES_FR)).reset_index(), hide_index=True, column_config={
        "Publisher": "Éditeur", "rang": "Rang",
        "MPI": st.column_config.ProgressColumn("MPI", min_value=0, max_value=100, format="%.1f"),
        "ventes": st.column_config.NumberColumn("Ventes (M)", format="%.0f"),
        "part_marche": st.column_config.NumberColumn("Part de marché / genre", format="percent"),
        "genres_leader": "Genres > 30 %", "leadership": "Marchés annuels dominés",
        "diversite": st.column_config.NumberColumn("Diversité", format="%.2f"),
        "constance": st.column_config.NumberColumn("Constance", format="%.2f"),
        "taux_hits": st.column_config.NumberColumn("Taux de hits", format="percent"),
        "n_titres": "Titres", "genre_principal": "Genre principal",
    })
    st.download_button("Télécharger le classement (CSV)", tableau.to_csv().encode("utf-8"), "market_power_index.csv", "text/csv")


# --------------------------------------------------------------------------------------
# 6. Explorateur de jeux et divergences
# --------------------------------------------------------------------------------------

def vue_jeux(ctx: dict) -> None:
    df = ctx["df"]
    entete("Explorateur de jeux", "Profil régional d'un titre et outliers culturels")
    if garde_vide(df):
        return
    ref = I.profil_marche(df)
    titres = I.titres(df).sort_values("Global_Sales", ascending=False)

    st.subheader("Profil régional d'un titre")
    nom = st.selectbox("Rechercher un titre", titres["Name"], index=0, key="jeu_nom",
                       help="Tapez quelques lettres pour filtrer. Les titres sont triés par ventes.")
    t = titres.set_index("Name").loc[nom]
    parts = t[C.REGIONS].astype(float) / t[C.REGIONS].sum()
    score = float(I.jensen_shannon(parts.to_numpy(), ref.to_numpy())[0])
    tuiles([
        ("Ventes mondiales", fr(t["Global_Sales"], 2) + " M", "Toutes plateformes"),
        ("Sortie", str(int(t["Year"])), "Première année de sortie"),
        ("Plateformes", str(int(t["n_plateformes"])), t["Plateformes"]),
        ("Divergence régionale", fr(score, 3), "0 = se vend exactement comme le marché ; 1 = maximum"),
    ])
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.plotly_chart(G.profil_regional(parts, ref), key="jeu_profil")
    with c2:
        st.markdown(f"**{t['Publisher']}** · {C.GENRES_FR.get(t['Genre'], t['Genre'])}")
        exces = (parts - ref).sort_values(ascending=False)
        st.markdown(f"Région la plus sur-représentée : **{NOMS_REG[exces.index[0]]}** "
                    f"({pct(parts[exces.index[0]], 0)} des ventes contre {pct(ref[exces.index[0]], 0)} pour le marché).")
        if t["Global_Sales"] < 0.5:
            st.info("Titre sous 0,5 M : les ventes étant arrondies au centième, son profil régional est peu fiable.")
        versions = df[df["Name"] == nom][["Platform_Name", "Year", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]]
        st.dataframe(versions.rename(columns={"Platform_Name": "Plateforme", "Year": "Année", "NA_Sales": "NA", "EU_Sales": "EU",
                                              "JP_Sales": "JP", "Other_Sales": "Autres", "Global_Sales": "Total"}),
                     hide_index=True, column_config={"Année": st.column_config.NumberColumn(format="%d")})

    st.subheader("Outliers culturels")
    c1, c2 = st.columns([1, 2])
    min_ventes = c1.select_slider("Ventes minimales du titre", [0.3, 0.5, 1.0, 2.0], value=0.5, format_func=lambda v: f"{fr(v, 1)} M", key="jeu_min")
    div = I.divergence_par_jeu(df, min_ventes=min_ventes)
    if len(div) < 10:
        st.warning("Trop peu de titres avec ces filtres.")
        return
    q1, q3 = div["divergence"].quantile([0.25, 0.75])
    seuil = q3 + 1.5 * (q3 - q1)
    c2.markdown(f"<br>{len(div)} titres analysés · seuil outlier (Q3 + 1,5 × IQR) = **{fr(seuil, 3)}** · "
                f"**{int(div['outlier'].sum())} outliers**", unsafe_allow_html=True)
    st.plotly_chart(G.nuage_outliers(div, seuil), key="jeu_nuage")

    region = st.pills("Région sur-représentée", list(C.REGIONS), default="JP_Sales", format_func=NOMS_REG.get, key="jeu_reg")
    o = div[div["outlier"] & (div["region_dominante"] == (region or "JP_Sales"))].nlargest(25, "Global_Sales").copy()
    parts_cols = ["part_NA_Sales", "part_EU_Sales", "part_JP_Sales", "part_Other_Sales"]
    o[parts_cols] = o[parts_cols] * 100
    o["Genre"] = o["Genre"].map(C.GENRES_FR)
    st.dataframe(o[["Name", "Year", "Genre", "Publisher", "Global_Sales", "part_NA_Sales", "part_EU_Sales", "part_JP_Sales", "part_Other_Sales", "divergence"]],
                 hide_index=True, column_config={
                     "Name": "Titre", "Year": st.column_config.NumberColumn("Année", format="%d"), "Publisher": "Éditeur",
                     "Global_Sales": st.column_config.NumberColumn("Ventes (M)", format="%.2f"),
                     "part_NA_Sales": st.column_config.NumberColumn("NA", format="%.0f %%"),
                     "part_EU_Sales": st.column_config.NumberColumn("EU", format="%.0f %%"),
                     "part_JP_Sales": st.column_config.NumberColumn("JP", format="%.0f %%"),
                     "part_Other_Sales": st.column_config.NumberColumn("Autres", format="%.0f %%"),
                     "divergence": st.column_config.ProgressColumn("Divergence", min_value=0, max_value=0.7, format="%.3f"),
                 })


# --------------------------------------------------------------------------------------
# 7. Qualité des données
# --------------------------------------------------------------------------------------

def vue_qualite(ctx: dict) -> None:
    raw, df_all, journal = ctx["raw"], ctx["df_all"], ctx["journal"]
    entete("Qualité des données", "Du fichier brut au jeu d'analyse : chaque correction est tracée")
    tuiles([
        ("Lignes brutes", fr(len(raw)), "vgsales.csv"),
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
    st.dataframe(df_all.head(500), hide_index=True, column_config={"Year": st.column_config.NumberColumn(format="%d")})
    st.download_button("Télécharger le jeu nettoyé (CSV)", df_all.to_csv(index=False).encode("utf-8"), "vgsales_clean.csv", "text/csv")


# --------------------------------------------------------------------------------------
# 8. Synthèse et conclusion
# --------------------------------------------------------------------------------------

GALERIE = {
    "I. Nettoyage": ["01"],
    "II. Analyse exploratoire": ["02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
    "II. Indicateurs avancés": ["13", "14", "15", "16", "17", "18", "19"],
    "III. Storytelling": ["20", "21", "22", "23", "24"],
}


def carte(chiffre: str, titre: str, texte: str) -> str:
    return (f"<div class='carte'><div class='carte-chiffre'>{chiffre}</div>"
            f"<div class='carte-titre'>{titre}</div><div class='carte-texte'>{texte}</div></div>")


def vue_conclusion(ctx: dict) -> None:
    df = ctx["df_all"]
    entete("Synthèse et conclusion", "Les résultats du projet en un coup d'œil, calculés sur l'ensemble du jeu nettoyé (1980-2016)")

    # Tous les chiffres sont recalculés ici : ils restent cohérents avec le notebook si les données changent.
    s = df["Global_Sales"].sort_values(ascending=False).to_numpy()
    top10_pct = s[: int(0.10 * len(s))].sum() / s.sum()
    annuel = df.groupby("Year")["Global_Sales"].sum()
    pic = int(annuel.loc[: C.ANNEE_MAX - 1].idxmax())
    constr = df.groupby("Manufacturer", observed=True)["Global_Sales"].sum() / s.sum()
    ps2 = df.loc[df["Platform"] == "PS2", "Global_Sales"].sum()
    d = df.assign(Periode=I.periode(df["Year"]))
    v = d.groupby(["Periode", "Genre"], observed=True)["Global_Sales"].sum().unstack("Genre")
    parts = v.div(v.sum(axis=1), axis=0)
    act_tir_avant = parts.loc["1995-1999", ["Action", "Shooter"]].sum()
    act_tir_apres = parts.loc["2010-2016", ["Action", "Shooter"]].sum()
    aff = I.affinite_genre_region(df)
    div = I.divergence_par_jeu(df, min_ventes=0.5)
    part_jp_outliers = (div.loc[div["outlier"], "region_dominante"] == "JP_Sales").mean()
    mpi = I.market_power_index(df)

    cartes = [
        (pct(top10_pct, 0), "Un marché de blockbusters",
         f"des ventes réalisées par 10 % des jeux. La médiane d'un jeu n'est que de {fr(df['Global_Sales'].median(), 2)} M d'exemplaires."),
        (f"{fr(annuel[pic], 0)} M", f"Un pic en {pic}",
         "puis un recul du physique : le dématérialisé et le mobile, absents de la source, prennent le relais."),
        (pct(constr["Sony"] + constr["Nintendo"], 0), "Le duopole Sony-Nintendo",
         f"des ventes de jeux sur leurs consoles. La PS2 reste la plateforme record ({fr(ps2, 0)} M de jeux)."),
        (f"{pct(act_tir_avant, 0)} → {pct(act_tir_apres, 0)}", "L'Action et le Tir prennent le pouvoir",
         "part des ventes mondiales entre 1995-1999 et 2010-2016, au détriment des Plates-formes et de la Course."),
        (f"×{fr(aff.loc['Role-Playing', 'JP_Sales'], 1)}", "Le Japon, un marché à part",
         f"d'affinité pour le RPG, ×{fr(aff.loc['Shooter', 'JP_Sales'], 2)} pour le Tir ; "
         f"{pct(part_jp_outliers, 0)} des outliers culturels sont japonais."),
        (f"{fr(mpi.loc['Nintendo', 'MPI'], 1)}/100", "Nintendo, hors catégorie",
         f"au Market Power Index, devant {mpi.index[1]} ({fr(mpi['MPI'].iloc[1], 1)}). "
         "Le pouvoir de marché récompense le taux de succès plus que la taille."),
    ]
    st.subheader("Six insights clés")
    for ligne in (cartes[:3], cartes[3:]):
        for col, c in zip(st.columns(3), ligne):
            col.markdown(carte(*c), unsafe_allow_html=True)

    gauche, droite = st.columns(2)
    with gauche:
        st.subheader("Difficultés de data wrangling")
        encart("""
        <ul>
        <li><b>Des problèmes invisibles</b> pour <code>isna()</code> et <code>duplicated()</code> : 149 fiches partielles « (JP sales) », doublons d'écriture, un jeu DS daté de 1985.</li>
        <li><b>Des étapes imbriquées</b> : une clé de jeu normalisée a été nécessaire pour imputer les années, puis fusionner les fiches.</li>
        <li><b>Fusionner sans double compter</b> : maximum par région plutôt que somme (<i>Ratchet &amp; Clank</i>).</li>
        <li><b>Des limites de la source</b> signalées plutôt que masquées : 2016 incomplète, dématérialisé absent, ventes européennes saisies en « reste du monde ».</li>
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
    st.caption("Les 24 graphiques interprétés du notebook, exportés en PNG dans le dossier figures/.")
    fichiers = {f.name[:2]: f for f in sorted(C.FIGURES_DIR.glob("*.png"))}
    if not fichiers:
        st.info("Aucune figure trouvée : exécutez le notebook pour les générer dans figures/.")
        return
    for onglet, (partie, numeros) in zip(st.tabs(list(GALERIE)), GALERIE.items()):
        with onglet:
            presentes = [fichiers[n] for n in numeros if n in fichiers]
            for i in range(0, len(presentes), 2):
                for col, f in zip(st.columns(2), presentes[i:i + 2]):
                    legende = f.stem[3:].replace("_", " ").replace("story ", "").capitalize()
                    col.image(str(f), caption=f"Figure {f.name[:2]} · {legende}", width="stretch")
