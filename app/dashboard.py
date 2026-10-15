"""Interface interactive du projet : streamlit run app/dashboard.py (ou python run_app.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from app import views
from modules import config as C
from modules.cleaning import nettoyer

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
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Nettoyage des données brutes...")
def charger() -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    raw = pd.read_csv(C.RAW_FILE)
    df, journal = nettoyer(raw)
    return raw, df, journal


raw, df_all, journal = charger()

# ------------------------------------------------------------------ filtres globaux
with st.sidebar:
    st.markdown("### 🎮 Ventes de jeux vidéo")
    st.markdown("<p class='note'>Projet final · Data Wrangling</p>", unsafe_allow_html=True)
    annees = st.slider("Période de sortie", 1980, 2016, (1980, 2016), key="f_annees")
    genres = st.multiselect("Genres", sorted(C.GENRES_FR), format_func=C.GENRES_FR.get, placeholder="Tous les genres", key="f_genres")
    constructeurs = st.multiselect("Constructeurs", C.ORDRE_CONSTRUCTEURS, placeholder="Tous les constructeurs", key="f_constr")
    types = st.multiselect("Type de plateforme", ["Salon", "Portable", "PC"], placeholder="Tous les types", key="f_types")

masque = df_all["Year"].between(*annees)
if genres:
    masque &= df_all["Genre"].isin(genres)
if constructeurs:
    masque &= df_all["Manufacturer"].isin(constructeurs)
if types:
    masque &= df_all["Platform_Type"].isin(types)
df = df_all[masque]
filtre_actif = bool(genres or constructeurs or types or annees != (1980, 2016))

with st.sidebar:
    if filtre_actif:
        st.info(f"Filtres actifs : {len(df):,} jeux sur {len(df_all):,}".replace(",", " "))
    st.markdown("<p class='note'>Source : VGChartz (scraping fin 2016), ventes physiques en millions d'exemplaires. "
                "Les données sont nettoyées au lancement par le même module que le notebook.</p>", unsafe_allow_html=True)

ctx = {"df": df, "df_all": df_all, "raw": raw, "journal": journal, "filtre_actif": filtre_actif}

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
st.navigation(pages).run()
