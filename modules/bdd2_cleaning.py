"""Pipeline de nettoyage de la deuxième base : bdd2_metacritic.csv (notes Metacritic).

Même ordre que bdd1_cleaning.py (structure -> valeurs manquantes -> types -> doublons -> préparation).
Les règles déjà écrites pour bdd1_vgsales.csv (années, éditeurs, fiches partielles) sont réutilisées
telles quelles : les deux bases sortent du même scraping VGChartz et ont les mêmes défauts.

Les ventes de cette base ne sont pas conservées : elles font doublon avec bdd1_vgsales_clean.csv,
qui reste la seule source de vérité pour les ventes. Le fichier propre garde l'identité du jeu
(nom, plateforme, année, genre, éditeur) et l'apport de Metacritic.
"""

from __future__ import annotations

import pandas as pd

from .bdd1_cleaning import (
    EDITEURS_ALIAS,
    MOTIF_FICHE_PARTIELLE,
    cle_jeu,
    corriger_annees_plateforme,
    imputer_annees,
    nom_sans_suffixe,
    traiter_editeurs,
)
from .config import ANNEE_MAX, ESRB_LABELS, PLATEFORMES, RATINGS_RAW_FILE

COLONNES_TEXTE = ["Name", "Platform", "Genre", "Publisher", "Developer", "Rating"]
NOTES = ["Critic_Score", "Critic_Count", "User_Score", "User_Count"]
METACRITIC = NOTES + ["Developer", "Rating"]

# Valeurs de remplacement des informations Metacritic absentes.
DEV_INCONNU = "Inconnu"
NON_CLASSE = "Non classé"

# Seuils de fiabilité : en dessous, la note repose sur trop peu d'avis pour être représentative.
SEUIL_CRITIQUES = 5
SEUIL_VOTES = 10


# --------------------------------------------------------------------------------------
# Étape 2 : valeurs manquantes
# --------------------------------------------------------------------------------------

def remplacer_tbd(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """"tbd" (to be determined) : pas encore assez de votes. Ce n'est pas une note -> manquant."""
    df = df.copy()
    tbd = df["User_Score"] == "tbd"
    df["User_Score"] = pd.to_numeric(df["User_Score"].where(~tbd), errors="coerce")
    return df, int(tbd.sum())


def traiter_classification(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """K-A (Kids to Adults) est l'ancien nom de E jusqu'en 1998 : même catégorie.
    Vide et RP (Rating Pending) : aucune classification connue -> "Non classé"."""
    df = df.copy()
    nb_ka = int((df["Rating"] == "K-A").sum())
    sans = df["Rating"].isna() | (df["Rating"] == "RP")
    df["Rating"] = df["Rating"].replace("K-A", "E").where(~sans, NON_CLASSE)
    return df, nb_ka, int(sans.sum())


# --------------------------------------------------------------------------------------
# Étape 4 : doublons et fausses correspondances
# --------------------------------------------------------------------------------------

def fusionner_fiches(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Une ligne par jeu (clé normalisée, plateforme, année), comme dans bdd1_cleaning.py.

    Les fiches sont triées pour que la fiche principale passe en premier (sans suffixe
    "(... sales)", éditeur connu, ventes les plus fortes). Pour chaque colonne Metacritic,
    on garde la première valeur renseignée : une fiche partielle peut porter la note
    quand la fiche principale ne l'a pas."""
    df = df.copy()
    df["_partielle"] = df["Name"].str.contains(MOTIF_FICHE_PARTIELLE, case=False, regex=True)
    df["_inconnu"] = df["Publisher"] == "Inconnu"
    df["_cle"] = cle_jeu(df["Name"])
    df["Name"] = nom_sans_suffixe(df["Name"])
    nb_renommees = int(df["_partielle"].sum())

    # Les valeurs de remplacement ne doivent pas l'emporter sur une vraie valeur d'une autre fiche.
    df["Developer"] = df["Developer"].replace(DEV_INCONNU, pd.NA)
    df["Rating"] = df["Rating"].replace(NON_CLASSE, pd.NA)

    df = df.sort_values(["_partielle", "_inconnu", "Global_Sales"], ascending=[True, True, False])
    colonnes = ["Name", "Genre", "Publisher"] + METACRITIC
    fusion = df.groupby(["_cle", "Platform", "Year"], as_index=False, sort=False)[colonnes].first()
    fusion["Developer"] = fusion["Developer"].fillna(DEV_INCONNU)
    fusion["Rating"] = fusion["Rating"].fillna(NON_CLASSE)
    return fusion, nb_renommees, len(df) - len(fusion)


def retirer_notes_ambigues(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Homonymes (remake, réédition) : même titre et même plateforme, années différentes, mais une
    seule et même note. Le scraping Metacritic a relié les deux jeux à la même fiche
    (ex. Need for Speed: Most Wanted 2005 et son remake de 2012). Impossible de savoir à quel jeu
    appartient la note : on la retire des deux plutôt que d'en attribuer une fausse."""
    df = df.copy()
    notes = df.dropna(subset=["Critic_Score"])
    groupes = notes.groupby(["_cle", "Platform"]).agg(
        annees=("Year", "nunique"), notes=("Critic_Score", "nunique"))
    ambigus = groupes[(groupes["annees"] > 1) & (groupes["notes"] == 1)].index
    masque = pd.MultiIndex.from_frame(df[["_cle", "Platform"]]).isin(ambigus)
    df.loc[masque, NOTES] = pd.NA
    df.loc[masque, "Developer"] = DEV_INCONNU
    df.loc[masque, "Rating"] = NON_CLASSE
    return df, int(masque.sum())


# --------------------------------------------------------------------------------------
# Étape 5 : préparation
# --------------------------------------------------------------------------------------

def enrichir(df: pd.DataFrame) -> pd.DataFrame:
    """Colonnes d'analyse : note joueurs sur 100, écart presse/joueurs, fiabilité des notes,
    studio principal, libellé ESRB, informations plateforme, décennie."""
    df = df.copy()
    for col in ["Critic_Count", "User_Count"]:
        df[col] = df[col].astype("Int64")
    df["User_Score_100"] = (df["User_Score"] * 10).round(0)
    df["Ecart_Presse_Joueurs"] = df["Critic_Score"] - df["User_Score_100"]
    df["Note_Presse_Fiable"] = df["Critic_Count"] >= SEUIL_CRITIQUES
    df["Note_Joueurs_Fiable"] = df["User_Count"] >= SEUIL_VOTES
    for col in ["Note_Presse_Fiable", "Note_Joueurs_Fiable"]:
        df[col] = df[col].fillna(False).astype(bool)
    # "Ubisoft Montreal, Ubisoft" -> studio principal = le premier cité.
    df["Developer_Main"] = df["Developer"].str.split(",").str[0].str.strip()
    df["Rating_Label"] = df["Rating"].map(ESRB_LABELS).fillna(NON_CLASSE)
    infos = pd.DataFrame.from_dict(
        PLATEFORMES,
        orient="index",
        columns=["Platform_Name", "Manufacturer", "Platform_Type", "Generation", "Platform_Launch"],
    )
    df = df.join(infos[["Platform_Name", "Manufacturer", "Platform_Type", "Generation"]], on="Platform")
    df["Decade"] = (df["Year"] // 10 * 10).astype(int)
    colonnes = ["Name", "Platform", "Year", "Genre", "Publisher",
                "Critic_Score", "Critic_Count", "User_Score", "User_Count", "User_Score_100",
                "Ecart_Presse_Joueurs", "Note_Presse_Fiable", "Note_Joueurs_Fiable",
                "Developer", "Developer_Main", "Rating", "Rating_Label",
                "Platform_Name", "Manufacturer", "Platform_Type", "Generation", "Decade"]
    return df.sort_values(["Critic_Score", "Name"], ascending=[False, True]).reset_index(drop=True)[colonnes]


def nettoyer(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Applique toutes les règles de nettoyage. Renvoie le jeu propre et le journal des étapes."""
    journal: list[dict] = []

    def noter(etape: str, detail: str, avant: int, apres: int) -> None:
        journal.append({"Étape": etape, "Détail": detail, "Lignes avant": avant,
                        "Lignes après": apres, "Écart": apres - avant})

    df = raw.rename(columns={"Year_of_Release": "Year"}).copy()
    for col in COLONNES_TEXTE:
        df[col] = df[col].str.strip()

    # 1. Structure
    n = len(df)
    df = df.dropna(subset=["Name"])
    noter("1. Jeu sans nom", "Ni nom ni genre : impossible à identifier ou à relier, aucune note", n, len(df))

    # 2. Valeurs manquantes
    n = len(df)
    df, nb_tbd = remplacer_tbd(df)
    noter("2. Note joueurs 'tbd'", f"{nb_tbd} valeurs 'tbd' (pas assez de votes) -> manquantes ; "
          "colonne convertie en nombre", n, len(df))
    noter("2. Notes manquantes", f"{int(df['Critic_Score'].isna().sum())} notes presse et "
          f"{int(df['User_Score'].isna().sum())} notes joueurs absentes : non imputées "
          "(Metacritic ne couvre que les plateformes récentes)", n, len(df))
    df, nb_inconnus = traiter_editeurs(df)
    noter("2. Éditeur manquant", f"{nb_inconnus} lignes (vides + 'Unknown') regroupées sous 'Inconnu'", n, len(df))
    nb_dev = int(df["Developer"].isna().sum())
    df["Developer"] = df["Developer"].fillna(DEV_INCONNU)
    noter("2. Développeur manquant", f"{nb_dev} lignes -> '{DEV_INCONNU}'", n, len(df))
    df, nb_ka, nb_sans = traiter_classification(df)
    noter("2. Classification ESRB", f"{nb_sans} lignes vides ou 'RP' -> '{NON_CLASSE}' ; "
          f"{nb_ka} 'K-A' -> 'E' (ancien nom)", n, len(df))
    df, via_jumelle, via_titre = imputer_annees(df)
    noter("2. Année manquante (imputée)", f"{via_jumelle} via une fiche jumelle de la même plateforme, "
          f"{via_titre} via le même titre sur les autres plateformes", n, len(df))
    n = len(df)
    df = df.dropna(subset=["Year"])
    noter("2. Année manquante (supprimée)", "Aucune source fiable pour dater le jeu", n, len(df))

    # 3. Types et cohérence
    nb_alias = int(df["Publisher"].isin(EDITEURS_ALIAS).sum())
    df["Publisher"] = df["Publisher"].replace(EDITEURS_ALIAS)
    noter("3. Libellés d'éditeurs", f"{nb_alias} lignes de filiales rattachées à leur groupe", len(df), len(df))
    n = len(df)
    df = df[df["Year"] <= ANNEE_MAX]
    noter("3. Années hors période", f"Sorties après {ANNEE_MAX} (scraping de fin 2016)", n, len(df))
    n = len(df)
    df, nb_corrigees, nb_impossibles = corriger_annees_plateforme(df)
    noter("3. Année avant la console", f"{nb_corrigees} années ramenées au lancement (écart d'un an), "
          f"{nb_impossibles} jeux impossibles supprimés", n, len(df))
    df["Year"] = df["Year"].astype(int)

    # 4. Doublons et fausses correspondances
    n = len(df)
    df, nb_renommees, nb_supprimees = fusionner_fiches(df)
    noter("4. Doublons et fiches partielles", f"{nb_renommees} noms suffixés '(... sales)' corrigés ; "
          f"{nb_supprimees} fiches fusionnées (première valeur renseignée par colonne)", n, len(df))
    df, nb_ambigus = retirer_notes_ambigues(df)
    noter("4. Notes ambiguës (homonymes)", f"{nb_ambigus} lignes : même titre et plateforme, années "
          "différentes, une seule note -> note retirée", len(df), len(df))

    # 5. Préparation
    df = enrichir(df)
    noter("5. Préparation", f"Note joueurs sur 100, écart presse/joueurs, fiabilité (>= {SEUIL_CRITIQUES} "
          f"critiques, >= {SEUIL_VOTES} votes), studio principal, libellé ESRB, plateforme, décennie",
          len(df), len(df))
    return df, journal


def charger_notes_propres(chemin=RATINGS_RAW_FILE) -> pd.DataFrame:
    """Raccourci utilisé par l'interface : brut -> propre."""
    return nettoyer(pd.read_csv(chemin))[0]
