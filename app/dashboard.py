"""Interface interactive du projet : streamlit run app/dashboard.py (ou python run_app.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app import donnees as D
from app import views
from modules import config as C
from modules import indicators as I

st.set_page_config(page_title="Ventes mondiales de jeux vidéo", page_icon="🎮", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2.2rem; max-width: 1350px;}
h1.titre {font-size: 2.0rem; font-weight: 700; margin-bottom: 0; letter-spacing: -0.01em;}
p.sous-titre {color: #52514e; font-size: 1.02rem; margin-top: 0.2rem; margin-bottom: 1.4rem;}
h2, h3 {letter-spacing: -0.01em;}
div[data-testid="stMetric"] {background: #ffffff; border-radius: 10px;}
div[data-testid="stMetricValue"] {font-size: 1.55rem;}
.encart {background: #f3f6fb; border-left: 3px solid #2a78d6; border-radius: 6px; padding: 0.8rem 1.1rem;
         color: #2b2b29; margin: 0.4rem 0 1.2rem 0; font-size: 0.97rem;}
.encart ol, .encart ul {margin: 0; padding-left: 1.2rem;} .encart li {margin: 0.25rem 0;}
.carte {background: #ffffff; border: 1px solid #e1e0d9; border-radius: 10px; padding: 1rem 1.1rem; min-height: 175px; margin-bottom: 1rem;}
.carte-chiffre {font-size: 1.7rem; font-weight: 700; color: #2a78d6; letter-spacing: -0.01em;}
.carte-titre {font-weight: 600; color: #0b0b0b; margin: 0.15rem 0 0.3rem 0;}
.carte-texte {color: #52514e; font-size: 0.92rem; line-height: 1.4;}
section[data-testid="stSidebar"] .note {font-size: 0.82rem; color: #6b6a66;}
.astuce {color: #6b6a66; font-size: 0.86rem; margin: -0.4rem 0 0.6rem 0;}
.zoom {background: #ffffff; border: 1px solid #e1e0d9; border-radius: 10px; padding: 0.9rem 1.1rem;}
.carte {transition: transform .15s ease, box-shadow .15s ease;}
.carte:hover {transform: translateY(-2px); box-shadow: 0 6px 18px rgba(11,11,11,.07);}
div[data-testid="stPlotlyChart"] {transition: opacity .2s ease;}
</style>
""", unsafe_allow_html=True)


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
    **{f"w_{k}": 20 for k in I.COMPOSANTES},
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
    "Données": [
        st.Page(lambda: views.vue_qualite(ctx), title="Qualité des données", icon="🧹", url_path="qualite"),
    ],
    "Résultats": [
        st.Page(lambda: views.vue_conclusion(ctx), title="Synthèse et conclusion", icon="🏁", url_path="conclusion"),
    ],
}
# Pages indexées par leur chemin (la page par défaut a un url_path vide pour Streamlit, d'où ce relevé à part).
ctx["ordre"] = ["accueil", "tendances", "genres", "regions", "mpi", "jeux", "qualite", "conclusion"]
ctx["pages"] = dict(zip(ctx["ordre"], (p for groupe in pages.values() for p in groupe)))
st.navigation(pages).run()
