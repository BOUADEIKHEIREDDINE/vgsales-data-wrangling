"""Jointure des ventes (vgsales_clean) et des notes Metacritic (video_games_ratings_clean),
puis Market Power Index enrichi d'une composante "qualité perçue".

Les deux bases sortent du même scraping VGChartz : la clé de nettoyage (nom normalisé,
plateforme, année) est donc aussi la clé de jointure. Les ventes viennent toujours de
vgsales_clean, les notes de la deuxième base.
"""

from __future__ import annotations

import pandas as pd

from . import indicators as I
from .cleaning import cle_jeu

CLE = ["_cle", "Platform", "Year"]
COLONNES_NOTES = ["Critic_Score", "Critic_Count", "User_Score_100", "User_Count", "Ecart_Presse_Joueurs",
                  "Note_Presse_Fiable", "Note_Joueurs_Fiable", "Developer", "Developer_Main",
                  "Rating", "Rating_Label"]

COMPOSANTES_QUALITE = I.COMPOSANTES | {"qualite": "Qualité perçue (note presse)"}
POIDS_QUALITE = {k: 1 / len(COMPOSANTES_QUALITE) for k in COMPOSANTES_QUALITE}

# En dessous de cette part de jeux notés, la note moyenne d'un éditeur n'est pas représentative.
COUVERTURE_MIN = 0.30
NOTES_MIN = 5


def joindre(ventes: pd.DataFrame, notes: pd.DataFrame) -> pd.DataFrame:
    """Jointure à gauche : tous les jeux de vgsales_clean, enrichis des notes quand elles existent."""
    v = ventes.assign(_cle=cle_jeu(ventes["Name"].astype(str)))
    n = notes.assign(_cle=cle_jeu(notes["Name"].astype(str)))[CLE + COLONNES_NOTES]
    joint = v.merge(n, on=CLE, how="left", indicator="_m", validate="one_to_one")
    joint["Relie"] = joint["_m"] == "both"
    joint["Note_Presse"] = joint["Critic_Score"].notna()
    return joint.drop(columns=["_cle", "_m"])


def bilan_jointure(joint: pd.DataFrame, notes: pd.DataFrame) -> pd.DataFrame:
    """Taux de correspondance en nombre de jeux et en part des ventes."""
    total = joint["Global_Sales"].sum()
    lignes = {
        "Jeux de vgsales_clean": (len(joint), total),
        "reliés à la base Metacritic": (joint["Relie"].sum(), joint.loc[joint["Relie"], "Global_Sales"].sum()),
        "dont avec une note presse": (joint["Note_Presse"].sum(), joint.loc[joint["Note_Presse"], "Global_Sales"].sum()),
        "non reliés": ((~joint["Relie"]).sum(), joint.loc[~joint["Relie"], "Global_Sales"].sum()),
    }
    bilan = pd.DataFrame(lignes, index=["Jeux", "Ventes (M)"]).T
    bilan["Part des jeux"] = bilan["Jeux"] / len(joint)
    bilan["Part des ventes"] = bilan["Ventes (M)"] / total
    bilan.loc["Jeux Metacritic absents de vgsales_clean"] = [len(notes) - joint["Relie"].sum(), None, None, None]
    return bilan


def qualite_editeurs(joint: pd.DataFrame) -> pd.DataFrame:
    """Note presse moyenne de chaque éditeur, pondérée par les ventes (un succès compte plus qu'un
    jeu confidentiel), sur les notes fiables. Couverture insuffisante -> note neutre (médiane)."""
    fiables = joint[joint["Note_Presse_Fiable"].fillna(False).astype(bool)]
    ponderee = (fiables["Critic_Score"] * fiables["Global_Sales"]).groupby(fiables["Publisher"]).sum()
    q = pd.DataFrame({
        "qualite_brute": ponderee / fiables.groupby("Publisher")["Global_Sales"].sum(),
        "n_notes": fiables.groupby("Publisher").size(),
        "couverture": joint.groupby("Publisher")["Note_Presse"].mean(),
    })
    q["n_notes"] = q["n_notes"].fillna(0).astype(int)
    q["qualite_representative"] = (q["couverture"] >= COUVERTURE_MIN) & (q["n_notes"] >= NOTES_MIN)
    return q


def market_power_index_qualite(joint: pd.DataFrame, poids: dict | None = None, min_titres: int = 20,
                               seuil_leader: float = 0.30) -> pd.DataFrame:
    """MPI à 6 composantes : les 5 de indicators.py + la qualité perçue. Même normalisation min-max."""
    poids = poids or POIDS_QUALITE
    total = sum(poids.values())
    res = I.composantes_mpi(joint, min_titres, seuil_leader).join(qualite_editeurs(joint))
    representative = res["qualite_representative"].fillna(False).astype(bool)
    res["qualite_representative"] = representative
    res["qualite"] = res["qualite_brute"].where(representative)
    res["qualite"] = res["qualite"].fillna(res["qualite"].median())
    for k in COMPOSANTES_QUALITE:
        res[f"{k}_norm"] = I.min_max(res[k])
    res["MPI"] = 100 * sum(poids[k] / total * res[f"{k}_norm"] for k in COMPOSANTES_QUALITE)
    res = res.sort_values("MPI", ascending=False)
    res.insert(0, "rang", range(1, len(res) + 1))
    return res
