"""Chargement, filtrage et calculs mis en cache : chaque combinaison de filtres n'est calculée qu'une fois."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules import config as C
from modules import bdd1_indicators as I
from modules import bdd2_jointure as J
from modules.bdd1_cleaning import nettoyer
from modules.bdd2_cleaning import nettoyer as nettoyer_notes

# Clé de filtres : (période, genres, constructeurs, types), tuples triés pour être hachables et stables.
Cle = tuple[tuple[int, int], tuple[str, ...], tuple[str, ...], tuple[str, ...]]
CLE_COMPLETE: Cle = ((1980, C.ANNEE_MAX), (), (), ())


# Réglages qui survivent aux changements de page. Streamlit efface l'état d'un widget dès qu'il n'est plus
# affiché ; la valeur est donc gardée à part (« _memo_<nom> ») et redonnée au widget à sa création. Quand le code
# change la valeur (clic sur un graphique, préréglage...), la clé du widget change de version pour qu'il soit
# recréé avec la nouvelle valeur : réécrire l'état d'un widget existant désynchronise son affichage.

def valeur(nom: str):
    return st.session_state.get(f"_memo_{nom}")


def definir(nom: str, v) -> None:
    etat = st.session_state
    if etat.get(f"_memo_{nom}") != v or f"_memo_{nom}" not in etat:
        etat[f"_memo_{nom}"] = v
        etat[f"_v_{nom}"] = etat.get(f"_v_{nom}", 0) + 1


def initialiser(defauts: dict) -> None:
    for nom, v in defauts.items():
        st.session_state.setdefault(f"_memo_{nom}", v)


def persistant(fabrique, nom: str, label: str, *args, param: str = "value", **kwargs):
    """Crée le widget `fabrique` (st.slider, st.selectbox...) avec la valeur mémorisée sous `nom`."""
    etat = st.session_state
    cle = f"{nom}__{etat.get(f'_v_{nom}', 0)}"

    def garder() -> None:
        etat[f"_memo_{nom}"] = etat[cle]

    v = etat.get(f"_memo_{nom}")
    if param == "index":
        options = list(args[0] if args else kwargs["options"])
        kwargs["index"] = options.index(v) if v in options else 0
    elif v is not None:
        kwargs[param] = v
    return fabrique(label, *args, key=cle, on_change=garder, **kwargs)


@st.cache_data(show_spinner="Nettoyage des données brutes...")
def charger() -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    raw = pd.read_csv(C.RAW_FILE)
    df, journal = nettoyer(raw)
    return raw, df, journal


@st.cache_data(show_spinner=False, max_entries=64)
def filtrer(cle: Cle) -> pd.DataFrame:
    (debut, fin), genres, constructeurs, types = cle
    df = charger()[1]
    masque = df["Year"].between(debut, fin)
    if genres:
        masque &= df["Genre"].isin(genres)
    if constructeurs:
        masque &= df["Manufacturer"].isin(constructeurs)
    if types:
        masque &= df["Platform_Type"].isin(types)
    return df[masque]


@st.cache_data(show_spinner=False, max_entries=64)
def titres(cle: Cle) -> pd.DataFrame:
    return I.titres(filtrer(cle)).sort_values("Global_Sales", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner=False, max_entries=64)
def divergences(cle: Cle, min_ventes: float) -> pd.DataFrame:
    return I.divergence_par_jeu(filtrer(cle), min_ventes=min_ventes)


@st.cache_data(show_spinner=False, max_entries=128)
def mpi(cle: Cle, poids: tuple[tuple[str, int], ...], min_titres: int, normalisation: str) -> pd.DataFrame:
    return I.market_power_index(filtrer(cle), poids=dict(poids), min_titres=min_titres, normalisation=normalisation)


# --------------------------------------------------------------------------------------
# Deuxième base : notes Metacritic, reliées aux ventes
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner="Nettoyage de la base Metacritic...")
def charger_notes() -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    raw = pd.read_csv(C.RATINGS_RAW_FILE)
    notes, journal = nettoyer_notes(raw)
    return raw, notes, journal


@st.cache_data(show_spinner=False)
def joint_complet() -> pd.DataFrame:
    return J.joindre(charger()[1], charger_notes()[1])


@st.cache_data(show_spinner=False, max_entries=64)
def joint(cle: Cle) -> pd.DataFrame:
    """Ventes + notes, avec les mêmes filtres que les ventes (la jointure garde l'index des ventes)."""
    return joint_complet().loc[filtrer(cle).index]


@st.cache_data(show_spinner=False, max_entries=128)
def mpi_qualite(cle: Cle, poids: tuple[tuple[str, int], ...], min_titres: int) -> pd.DataFrame:
    return J.market_power_index_qualite(joint(cle), poids=dict(poids), min_titres=min_titres)
