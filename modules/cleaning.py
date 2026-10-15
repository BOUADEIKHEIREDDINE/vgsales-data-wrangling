"""Pipeline de nettoyage du fichier vgsales.csv.

Le notebook détaille chaque étape cellule par cellule, dans l'ordre du sujet
(valeurs manquantes -> types -> doublons -> préparation). Ce module rejoue exactement
les mêmes règles pour que l'interface travaille sur des données identiques.
"""

from __future__ import annotations

import pandas as pd

from .config import ANNEE_MAX, PLATEFORMES, RAW_FILE, REGIONS

COLONNES_TEXTE = ["Name", "Platform", "Genre", "Publisher"]
VENTES = REGIONS + ["Global_Sales"]

# Fiches de ventes partielles du scraping VGChartz : "Naruto (JP sales)", "Ratchet (Weekly american sales)"...
MOTIF_FICHE_PARTIELLE = r"\s*\((?:[^()]*sales)\)\s*$"

# Filiales régionales ou labels d'un même groupe. Les fusions historiques entre sociétés
# indépendantes (SquareSoft + Enix -> Square Enix en 2003) sont volontairement conservées.
EDITEURS_ALIAS = {
    "Sony Computer Entertainment America": "Sony Computer Entertainment",
    "Sony Computer Entertainment Europe": "Sony Computer Entertainment",
    "Ubisoft Annecy": "Ubisoft",
    "Electronic Arts Victor": "Electronic Arts",
    "Activision Value": "Activision",
    "Activision Blizzard": "Activision",
    "Valve": "Valve Software",
    "Codemasters Online": "Codemasters",
    "Hudson Entertainment": "Hudson Soft",
}


def nom_sans_suffixe(noms: pd.Series) -> pd.Series:
    """Retire le suffixe "(JP sales)", "(Weekly american sales)"... d'un nom de jeu."""
    return noms.str.replace(MOTIF_FICHE_PARTIELLE, "", case=False, regex=True).str.strip()


def cle_jeu(noms: pd.Series) -> pd.Series:
    """Identifiant d'un jeu insensible à la casse, à la ponctuation et aux suffixes de fiche :
    "wwe Smackdown vs. Raw 2006" et "WWE SmackDown! vs. RAW 2006" donnent la même clé."""
    return nom_sans_suffixe(noms).str.lower().str.replace(r"[^a-z0-9]", "", regex=True)


# --------------------------------------------------------------------------------------
# Étape 2 : valeurs manquantes
# --------------------------------------------------------------------------------------

def traiter_editeurs(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Éditeur vide + modalité "Unknown" existante -> une seule modalité "Inconnu"."""
    df = df.copy()
    nb_inconnus = int(df["Publisher"].isna().sum() + (df["Publisher"] == "Unknown").sum())
    df["Publisher"] = df["Publisher"].fillna("Unknown").replace("Unknown", "Inconnu")
    return df, nb_inconnus


def annees_de_reference(df: pd.DataFrame, cles: list[str]) -> pd.Series:
    """Année retenue pour chaque clé, seulement quand toutes les fiches datées sont d'accord."""
    connues = df.dropna(subset=["Year"]).groupby(cles)["Year"].agg(["nunique", "first"])
    return connues.loc[connues["nunique"] == 1, "first"]


def imputer_annees(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Deux sources fiables, dans cet ordre :
    1. une fiche jumelle datée (même jeu, même plateforme : doublon ou fiche partielle) ;
    2. le même titre sur les autres plateformes, si elles donnent toutes la même année."""
    df = df.copy()
    df["_cle"] = cle_jeu(df["Name"])

    manque = df["Year"].isna()
    jumelle = annees_de_reference(df, ["_cle", "Platform"])
    via_jumelle = pd.Series(list(zip(df.loc[manque, "_cle"], df.loc[manque, "Platform"])),
                            index=df.index[manque]).map(jumelle)
    df.loc[manque, "Year"] = via_jumelle

    manque = df["Year"].isna()
    titre = annees_de_reference(df, ["_cle"])
    via_titre = df.loc[manque, "_cle"].map(titre)
    df.loc[manque, "Year"] = via_titre
    return df.drop(columns="_cle"), int(via_jumelle.notna().sum()), int(via_titre.notna().sum())


# --------------------------------------------------------------------------------------
# Étape 3 : types et cohérence des valeurs
# --------------------------------------------------------------------------------------

def corriger_annees_plateforme(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Un jeu ne peut pas sortir avant sa console. Écart d'un an : date de sortie régionale,
    on ramène l'année au lancement. Écart plus grand : erreur de saisie, on supprime."""
    df = df.copy()
    lancement = df["Platform"].map({k: v[4] for k, v in PLATEFORMES.items()})
    ecart = lancement - df["Year"]
    a_corriger = ecart == 1
    df.loc[a_corriger, "Year"] = lancement[a_corriger]
    return df[~(ecart > 1)], int(a_corriger.sum()), int((ecart > 1).sum())


# --------------------------------------------------------------------------------------
# Étape 4 : doublons
# --------------------------------------------------------------------------------------

def fusionner_fiches(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Regroupe toutes les fiches d'un même jeu (même clé, plateforme et année) : doublons exacts,
    fiches partielles "(JP sales)", doublons d'écriture, ventes éclatées sur deux lignes.

    Les ventes sont fusionnées en prenant le maximum par région : c'est la somme quand les fiches se
    complètent (l'une a 0 dans la région) et cela évite un double comptage quand elles se recouvrent
    (deux relevés de la même région). Les informations (nom, genre, éditeur) viennent de la fiche
    principale : sans suffixe, éditeur connu, ventes les plus fortes."""
    df = df.copy()
    df["_partielle"] = df["Name"].str.contains(MOTIF_FICHE_PARTIELLE, case=False, regex=True)
    df["_inconnu"] = df["Publisher"] == "Inconnu"
    df["_cle"] = cle_jeu(df["Name"])
    df["Name"] = nom_sans_suffixe(df["Name"])
    nb_renommees = int(df["_partielle"].sum())

    cles = ["_cle", "Platform", "Year"]
    df = df.sort_values(["_partielle", "_inconnu", "Global_Sales"], ascending=[True, True, False])
    regles = {c: "first" for c in ["Name", "Genre", "Publisher"]} | {r: "max" for r in REGIONS}
    fusion = df.groupby(cles, as_index=False, sort=False).agg(regles)
    multiples = df.groupby(cles, sort=False).size().to_numpy() > 1
    # Fiche unique : on garde son total d'origine. Fiches fusionnées : total recalculé.
    origine = df.groupby(cles, sort=False)["Global_Sales"].first().to_numpy()
    fusion["Global_Sales"] = fusion[REGIONS].sum(axis=1).round(2).where(multiples, origine)
    nb_supprimees = len(df) - len(fusion)
    return fusion[["Name", "Platform", "Year", "Genre", "Publisher"] + VENTES], nb_renommees, nb_supprimees


# --------------------------------------------------------------------------------------
# Étape 5 : préparation
# --------------------------------------------------------------------------------------

def enrichir(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes d'analyse : informations plateforme, décennie, rang recalculé."""
    df = df.copy()
    infos = pd.DataFrame.from_dict(
        PLATEFORMES,
        orient="index",
        columns=["Platform_Name", "Manufacturer", "Platform_Type", "Generation", "Platform_Launch"],
    )
    df = df.join(infos, on="Platform")
    df["Decade"] = (df["Year"] // 10 * 10).astype(int)
    df = df.sort_values(["Global_Sales", "Name"], ascending=[False, True]).reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))
    for col in ["Platform", "Genre", "Manufacturer", "Platform_Type"]:
        df[col] = df[col].astype("category")
    return df


def nettoyer(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Applique toutes les règles de nettoyage. Renvoie le jeu propre et le journal des étapes."""
    journal: list[dict] = []

    def noter(etape: str, detail: str, avant: int, apres: int) -> None:
        journal.append({"Étape": etape, "Détail": detail, "Lignes avant": avant,
                        "Lignes après": apres, "Écart": apres - avant})

    df = raw.drop(columns="Rank").copy()
    for col in COLONNES_TEXTE:
        df[col] = df[col].str.strip()

    # 2. Valeurs manquantes
    n = len(df)
    df, nb_inconnus = traiter_editeurs(df)
    noter("2. Éditeur manquant", f"{nb_inconnus} lignes (vides + 'Unknown') regroupées sous 'Inconnu'", n, len(df))
    df, via_jumelle, via_titre = imputer_annees(df)
    noter("2. Année manquante (imputée)", f"{via_jumelle} via une fiche jumelle de la même plateforme, "
          f"{via_titre} via le même titre sur les autres plateformes", n, len(df))
    n = len(df)
    df = df.dropna(subset=["Year"])
    noter("2. Année manquante (supprimée)", "Aucune source fiable pour dater le jeu", n, len(df))

    # 3. Types et cohérence
    nb_alias = int(df["Publisher"].isin(EDITEURS_ALIAS).sum())
    df["Publisher"] = df["Publisher"].replace(EDITEURS_ALIAS)
    noter("3. Libellés d'éditeurs", f"{nb_alias} lignes de filiales rattachées à leur groupe "
          f"({len(EDITEURS_ALIAS)} libellés)", len(df), len(df))
    n = len(df)
    df = df[df["Year"] <= ANNEE_MAX]
    noter("3. Années hors période", f"Sorties après {ANNEE_MAX} (scraping de fin 2016) : annonces et erreur", n, len(df))
    n = len(df)
    df, nb_corrigees, nb_impossibles = corriger_annees_plateforme(df)
    noter("3. Année avant la console", f"{nb_corrigees} années ramenées au lancement (écart d'un an), "
          f"{nb_impossibles} jeu impossible supprimé", n, len(df))
    df["Year"] = df["Year"].astype(int)

    # 4. Doublons
    n = len(df)
    df, nb_renommees, nb_supprimees = fusionner_fiches(df)
    noter("4. Doublons et fiches partielles", f"{nb_renommees} noms suffixés '(... sales)' corrigés ; "
          f"{nb_supprimees} fiches fusionnées dans la fiche principale (max par région)", n, len(df))

    # 5. Préparation
    df = enrichir(df)
    noter("5. Préparation", "Catégories, constructeur, type et génération de console, décennie, rang", len(df), len(df))
    return df, journal


def charger_donnees_propres(chemin=RAW_FILE) -> pd.DataFrame:
    """Raccourci utilisé par l'interface : brut -> propre."""
    return nettoyer(pd.read_csv(chemin))[0]
