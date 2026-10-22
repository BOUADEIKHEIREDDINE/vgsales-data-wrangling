"""Interface interactive du projet : streamlit run app/dashboard.py (ou python run_app.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app import theme  # avant charts / views : palette arcade des diapos
from app import donnees as D
from app import views
from modules import config as C
from modules import indicators as I
from modules import jointure as J

st.set_page_config(page_title="Ventes mondiales de jeux vidéo", page_icon="🎮", layout="wide")

st.markdown(theme.CSS, unsafe_allow_html=True)


raw, df_all, journal = D.charger()

PERIODE_COMPLETE = (1980, C.ANNEE_MAX)
RACCOURCIS = {
    "Tout": PERIODE_COMPLETE,
    "Années 80": (1980, 1989),
    "Années 90": (1990, 1999),
    "Ère PS2": (2000, 2005),
    "7e génération": (2006, 2012),
    "2013-2016": (2013, 2016),
}

# Filtres de la barre latérale : toujours affichés, ils gardent leur état ; leurs valeurs par défaut sont posées
# dans le Session State (et pas dans les widgets) pour que les raccourcis et la réinitialisation puissent les modifier.
FILTRES = {"f_annees": PERIODE_COMPLETE, "f_genres": [], "f_constr": [], "f_types": []}
for k, v in FILTRES.items():
    st.session_state.setdefault(k, v)

# Réglages des pages, conservés d'une page à l'autre (voir app/donnees.py).
D.initialiser({
    "ens_part": "Volume", "t_n": 20, "g_sel": ["Action", "Shooter", "Platform", "Role-Playing"],
    "r_mode": "Affinité (préférences)", "mpi_min": 20, "mpi_norm": "minmax", "mpi_n": 15,
    "jeu_min": 0.5, "jeu_reg": "JP_Sales", "c_galerie": "II. Analyse exploratoire",
    **{f"w_{k}": 20 for k in J.COMPOSANTES_QUALITE},
    "mpi_qualite": False, "g_notes": False, "n_mesure": "Ventes médianes", "n_sens": "Presse plus enthousiaste",
})


def appliquer_raccourci() -> None:
    choix = st.session_state.get("f_raccourci")
    if choix:
        st.session_state["f_annees"] = RACCOURCIS[choix]
        st.toast(f"Période : {choix} ({RACCOURCIS[choix][0]}-{RACCOURCIS[choix][1]})", icon="📅")
    st.session_state["f_raccourci"] = None


def reinitialiser() -> None:
    for k in ("f_annees", "f_genres", "f_constr", "f_types"):
        st.session_state[k] = FILTRES[k]
    st.toast("Filtres réinitialisés", icon="↺")


# ------------------------------------------------------------------ filtres globaux
with st.sidebar:
    st.markdown("### 🎮 Ventes de jeux vidéo")
    st.markdown("<p class='note'>Projet final · Data Wrangling</p>", unsafe_allow_html=True)
    annees = st.slider("Période de sortie", 1980, C.ANNEE_MAX, key="f_annees")
    st.pills("Raccourcis", list(RACCOURCIS), key="f_raccourci", on_change=appliquer_raccourci, label_visibility="collapsed")
    genres = st.multiselect("Genres", sorted(C.GENRES_FR), format_func=C.GENRES_FR.get, placeholder="Tous les genres", key="f_genres")
    constructeurs = st.multiselect("Constructeurs", C.ORDRE_CONSTRUCTEURS, placeholder="Tous les constructeurs", key="f_constr")
    types = st.multiselect("Type de plateforme", ["Salon", "Portable", "PC"], placeholder="Tous les types", key="f_types")

cle = (tuple(annees), tuple(sorted(genres)), tuple(sorted(constructeurs)), tuple(sorted(types)))
df = D.filtrer(cle)
filtre_actif = cle != D.CLE_COMPLETE

with st.sidebar:
    if filtre_actif:
        part = df["Global_Sales"].sum() / df_all["Global_Sales"].sum()
        st.info(f"**{len(df):,} jeux** sur {len(df_all):,} · {part:.0%} des ventes".replace(",", " ").replace("%", " %"))
        st.button("↺ Réinitialiser les filtres", on_click=reinitialiser, width="stretch")
    st.markdown("<p class='note'>Source : VGChartz (scraping fin 2016), ventes physiques en millions d'exemplaires. "
                "Les données sont nettoyées au lancement par le même module que le notebook.</p>", unsafe_allow_html=True)

ctx = {"df": df, "df_all": df_all, "raw": raw, "journal": journal, "filtre_actif": filtre_actif, "cle": cle}

pages = {
    "Analyse": [
        st.Page(lambda: views.vue_ensemble(ctx), title="Vue d'ensemble", icon="🏠", url_path="accueil", default=True),
        st.Page(lambda: views.vue_tendances(ctx), title="Tendances et plateformes", icon="📈", url_path="tendances"),
        st.Page(lambda: views.vue_genres(ctx), title="Genres", icon="🎯", url_path="genres"),
        st.Page(lambda: views.vue_regions(ctx), title="Régions", icon="🌍", url_path="regions"),
    ],
    "Indicateurs avancés": [
        st.Page(lambda: views.vue_mpi(ctx), title="Market Power Index", icon="🏆", url_path="mpi"),
        st.Page(lambda: views.vue_jeux(ctx), title="Explorateur de jeux", icon="🔎", url_path="jeux"),
    ],
    "Deuxième source": [
        st.Page(lambda: views.vue_notes(ctx), title="Notes Metacritic", icon="⭐", url_path="notes"),
    ],
    "Données": [
        st.Page(lambda: views.vue_qualite(ctx), title="Qualité des données", icon="🧹", url_path="qualite"),
    ],
    "Résultats": [
        st.Page(lambda: views.vue_conclusion(ctx), title="Synthèse et conclusion", icon="🏁", url_path="conclusion"),
    ],
}
# Pages indexées par leur chemin (la page par défaut a un url_path vide pour Streamlit, d'où ce relevé à part).
ctx["ordre"] = ["accueil", "tendances", "genres", "regions", "mpi", "jeux", "notes", "qualite", "conclusion"]
ctx["pages"] = dict(zip(ctx["ordre"], (p for groupe in pages.values() for p in groupe)))
st.navigation(pages).run()
