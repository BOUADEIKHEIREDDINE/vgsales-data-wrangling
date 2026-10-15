"""Indicateurs avancés : Market Power Index des éditeurs et divergences de préférences régionales."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import REGIONS, SEUIL_HIT

COMPOSANTES = {
    "part_marche": "Part de marché par genre",
    "leadership": "Leadership (> 30 % d'un genre)",
    "diversite": "Diversité des genres",
    "constance": "Constance régionale",
    "taux_hits": "Taux de succès (hits)",
}
POIDS_DEFAUT = {k: 0.2 for k in COMPOSANTES}

PERIODES = [(1980, 1994), (1995, 1999), (2000, 2004), (2005, 2009), (2010, 2016)]


# --------------------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------------------

def periode(annees: pd.Series) -> pd.Series:
    """Découpe les années en périodes de 5 ans (1980-1994 regroupées : peu de jeux)."""
    labels = [f"{a}-{b}" for a, b in PERIODES]
    bornes = [PERIODES[0][0] - 1] + [b for _, b in PERIODES]
    return pd.cut(annees, bins=bornes, labels=labels)


def entropie_normalisee(parts: pd.DataFrame) -> pd.Series:
    """Entropie de Shannon divisée par son maximum (log du nombre de colonnes) : 0 = un seul genre, 1 = parfaitement réparti."""
    p = parts.div(parts.sum(axis=1), axis=0).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -np.nansum(np.where(p > 0, p * np.log(p), 0.0), axis=1)
    return pd.Series(h / np.log(parts.shape[1]), index=parts.index)


def jensen_shannon(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Divergence de Jensen-Shannon en base 2 (bornée entre 0 et 1), ligne par ligne."""
    p = np.atleast_2d(p).astype(float)
    q = np.broadcast_to(np.atleast_2d(q).astype(float), p.shape)
    p = p / p.sum(axis=1, keepdims=True)
    q = q / q.sum(axis=1, keepdims=True)
    m = (p + q) / 2

    def kl(a, b):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.nansum(np.where(a > 0, a * np.log2(a / b), 0.0), axis=1)

    return (kl(p, m) + kl(q, m)) / 2


def min_max(s: pd.Series) -> pd.Series:
    etendue = s.max() - s.min()
    return (s - s.min()) / etendue if etendue > 0 else s * 0


# --------------------------------------------------------------------------------------
# Market Power Index
# --------------------------------------------------------------------------------------

def parts_genre(df: pd.DataFrame) -> pd.DataFrame:
    """Matrice éditeur x genre : part de l'éditeur dans les ventes mondiales du genre."""
    ventes = df.pivot_table(index="Publisher", columns="Genre", values="Global_Sales",
                            aggfunc="sum", fill_value=0, observed=True)
    return ventes / ventes.sum()


def leadership_annuel(df: pd.DataFrame, seuil: float = 0.30, min_jeux: int = 5) -> pd.Series:
    """Nombre de couples (genre, année) où l'éditeur dépasse `seuil` des ventes du genre.
    Les marchés genre-année de moins de `min_jeux` jeux sont ignorés (leader par défaut)."""
    g = df.groupby(["Genre", "Year", "Publisher"], observed=True)["Global_Sales"].sum()
    total = g.groupby(level=["Genre", "Year"], observed=True).transform("sum")
    taille = df.groupby(["Genre", "Year"], observed=True).size()
    part = (g / total).reset_index(name="part")
    part = part.join(taille.rename("n_jeux"), on=["Genre", "Year"])
    leaders = part[(part["part"] > seuil) & (part["n_jeux"] >= min_jeux)]
    return leaders.groupby("Publisher").size()


def composantes_mpi(df: pd.DataFrame, min_titres: int = 20, seuil_leader: float = 0.30) -> pd.DataFrame:
    """Calcule les 5 composantes brutes pour chaque éditeur éligible."""
    parts = parts_genre(df)
    ventes_genre = df.pivot_table(index="Publisher", columns="Genre", values="Global_Sales",
                                  aggfunc="sum", fill_value=0, observed=True)
    poids_portefeuille = ventes_genre.div(ventes_genre.sum(axis=1), axis=0)

    # Taux de hits au niveau du titre (toutes plateformes confondues) : un portage ne compte pas deux fois.
    titres = df.groupby(["Publisher", "Name"])["Global_Sales"].sum().reset_index()
    titres["hit"] = titres["Global_Sales"] >= SEUIL_HIT
    hits = titres.groupby("Publisher").agg(n_titres=("Name", "size"), n_hits=("hit", "sum"))

    # Parts de marché régionales de chaque éditeur.
    ventes_reg = df.groupby("Publisher")[REGIONS].sum()
    parts_reg = ventes_reg / ventes_reg.sum()
    cv = parts_reg.std(axis=1, ddof=0) / parts_reg.mean(axis=1)

    res = pd.DataFrame({
        "ventes": df.groupby("Publisher")["Global_Sales"].sum(),
        "part_marche_globale": df.groupby("Publisher")["Global_Sales"].sum() / df["Global_Sales"].sum(),
        "part_marche": (poids_portefeuille * parts).sum(axis=1),
        "genres_leader": (parts > seuil_leader).sum(axis=1),
        "leadership": leadership_annuel(df, seuil_leader),
        "n_genres": (ventes_genre > 0).sum(axis=1),
        "diversite": entropie_normalisee(ventes_genre),
        # Le CV de 4 valeurs positives est au plus sqrt(3) : la constance est donc bornée dans [0, 1].
        "constance": (1 - cv / np.sqrt(len(REGIONS) - 1)).clip(0, 1),
        "n_titres": hits["n_titres"],
        "n_hits": hits["n_hits"],
    })
    res["leadership"] = res["leadership"].fillna(0).astype(int)
    res["taux_hits"] = res["n_hits"] / res["n_titres"]
    res["genre_principal"] = ventes_genre.idxmax(axis=1)
    res["region_forte"] = (parts_reg.idxmax(axis=1))
    eligibles = (res["n_titres"] >= min_titres) & (res.index != "Inconnu")
    return res[eligibles]


def market_power_index(df: pd.DataFrame, poids: dict | None = None, min_titres: int = 20,
                       seuil_leader: float = 0.30, normalisation: str = "minmax") -> pd.DataFrame:
    """Score de 0 à 100 = somme pondérée des 5 composantes normalisées entre éditeurs éligibles."""
    poids = poids or POIDS_DEFAUT
    total = sum(poids.values())
    res = composantes_mpi(df, min_titres, seuil_leader)
    for k in COMPOSANTES:
        res[f"{k}_norm"] = min_max(res[k]) if normalisation == "minmax" else res[k].rank(pct=True)
    res["MPI"] = 100 * sum(poids[k] / total * res[f"{k}_norm"] for k in COMPOSANTES)
    res = res.sort_values("MPI", ascending=False)
    res.insert(0, "rang", range(1, len(res) + 1))
    return res


def sensibilite_mpi(composantes_norm: pd.DataFrame, n_tirages: int = 2000, top: int = 10,
                    graine: int = 42) -> pd.DataFrame:
    """Tire des pondérations aléatoires (Dirichlet uniforme) et mesure la stabilité du classement."""
    rng = np.random.default_rng(graine)
    poids = rng.dirichlet(np.ones(composantes_norm.shape[1]), size=n_tirages)
    scores = composantes_norm.to_numpy() @ poids.T
    rangs = pd.DataFrame(scores, index=composantes_norm.index).rank(ascending=False)
    return pd.DataFrame({
        "rang_median": rangs.median(axis=1),
        "rang_p10": rangs.quantile(0.10, axis=1),
        "rang_p90": rangs.quantile(0.90, axis=1),
        f"pct_top{top}": (rangs <= top).mean(axis=1) * 100,
    }).sort_values("rang_median")


# --------------------------------------------------------------------------------------
# Divergences régionales
# --------------------------------------------------------------------------------------

def profil_marche(df: pd.DataFrame) -> pd.Series:
    """Répartition régionale de l'ensemble du marché (profil de référence)."""
    v = df[REGIONS].sum()
    return v / v.sum()


def titres(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les versions d'un même titre sur toutes ses plateformes."""
    principal = df.sort_values("Global_Sales", ascending=False).groupby("Name").first()
    agg = df.groupby("Name").agg(
        **{r: (r, "sum") for r in REGIONS},
        Global_Sales=("Global_Sales", "sum"),
        Year=("Year", "min"),
        n_plateformes=("Platform", "nunique"),
        Plateformes=("Platform", lambda s: ", ".join(sorted(map(str, s.unique())))),
    )
    agg["Genre"] = principal["Genre"].astype(str)
    agg["Publisher"] = principal["Publisher"]
    return agg.reset_index()


def divergence_par_jeu(df: pd.DataFrame, min_ventes: float = 0.5) -> pd.DataFrame:
    """Score de divergence de chaque titre = Jensen-Shannon entre son profil régional et celui du marché.
    Seuil de ventes : les ventes sont arrondies à 0,01 M, les petits titres ont des profils trop bruités."""
    ref = profil_marche(df)
    t = titres(df)
    t = t[t["Global_Sales"] >= min_ventes].copy()
    somme = t[REGIONS].sum(axis=1)
    t = t[somme > 0]
    parts = t[REGIONS].div(t[REGIONS].sum(axis=1), axis=0)
    for r in REGIONS:
        t[f"part_{r}"] = parts[r]
    t["divergence"] = jensen_shannon(parts.to_numpy(), ref.to_numpy())
    # Région la plus sur-représentée : plus grand excès de part par rapport au profil du marché.
    exces = parts - ref
    t["region_dominante"] = exces.idxmax(axis=1)
    t["exces_max"] = exces.max(axis=1)
    q1, q3 = t["divergence"].quantile([0.25, 0.75])
    t["outlier"] = t["divergence"] > q3 + 1.5 * (q3 - q1)
    return t.sort_values("divergence", ascending=False).reset_index(drop=True)


def affinite_genre_region(df: pd.DataFrame) -> pd.DataFrame:
    """Indice d'affinité (lift) : poids du genre dans la région / poids du genre dans le monde.
    1 = comme la moyenne mondiale, 2 = deux fois plus présent, 0,5 = deux fois moins."""
    ventes = df.groupby("Genre", observed=True)[REGIONS + ["Global_Sales"]].sum()
    parts = ventes / ventes.sum()
    return parts[REGIONS].div(parts["Global_Sales"], axis=0)


def mix_genres_par_periode(df: pd.DataFrame) -> pd.DataFrame:
    """Part de chaque genre dans les ventes de chaque région, par période (format long)."""
    d = df.assign(Periode=periode(df["Year"]))
    v = d.groupby(["Periode", "Genre"], observed=True)[REGIONS].sum()
    parts = v / v.groupby(level="Periode", observed=True).transform("sum")
    return parts.reset_index().melt(id_vars=["Periode", "Genre"], var_name="Region", value_name="part")


def convergence_regionale(df: pd.DataFrame, annee_min: int = 1995) -> pd.DataFrame:
    """Jensen-Shannon entre les mix de genres de deux régions, année par année.
    Plus la valeur baisse, plus les goûts des deux régions se ressemblent."""
    d = df[df["Year"] >= annee_min]
    v = d.groupby(["Year", "Genre"], observed=True)[REGIONS].sum().unstack("Genre", fill_value=0)
    paires = [("NA_Sales", "EU_Sales"), ("NA_Sales", "JP_Sales"), ("EU_Sales", "JP_Sales")]
    out = {}
    for a, b in paires:
        out[f"{a}|{b}"] = jensen_shannon(v[a].to_numpy(), v[b].to_numpy())
    return pd.DataFrame(out, index=v.index)
