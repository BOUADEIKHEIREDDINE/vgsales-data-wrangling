# Ventes mondiales de jeux vidéo (1980-2016)

Projet final de Data Wrangling : nettoyage, analyse exploratoire, indicateurs avancés et interface interactive, à partir du fichier `vgsales.csv` (16 598 jeux, ventes en millions d'exemplaires, source VGChartz).

## Contenu

| Élément | Rôle |
|---|---|
| `projet_final.ipynb` | **Livrable principal.** Notebook exécuté : Partie I (nettoyage), Partie II (EDA, Market Power Index, divergences régionales), Partie III (storytelling), conclusion |
| `projet_final.html` | Le même notebook, lisible dans un navigateur sans Jupyter |
| `app/dashboard.py` | Interface web interactive (Streamlit), 8 pages |
| `modules/` | Code partagé : `cleaning.py` (règles de nettoyage), `indicators.py` (MPI, divergences), `config.py`, `viz.py` |
| `BDD_states/` | `vgsales.csv` (brut), `vgsales_clean.csv` (propre), `market_power_index.csv`, `divergence_regionale.csv` |
| `figures/` | Les 24 graphiques du notebook en PNG (pour un rapport ou une soutenance) |
| `brouillons/` | Les notebooks de travail d'origine, conservés tels quels |

## Installation

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

Un environnement `.venv` déjà prêt est fourni dans le dossier (Linux).

## Lancer le notebook

Ouvrir `projet_final.ipynb` dans Jupyter ou VS Code, puis *Run All*. Le notebook doit être exécuté depuis ce dossier (il importe `modules/`). Il régénère `vgsales_clean.csv`, les CSV d'indicateurs et les figures.

## Lancer l'interface

```bash
python run_app.py
```

puis ouvrir http://localhost:8501. Les pages :

- **Vue d'ensemble** : chiffres clés, ventes par constructeur, top 10, messages clés
- **Tendances et plateformes** : jeux et ventes par année, cycle de vie des consoles, classement
- **Genres** : fréquence contre ventes, évolution, leaders par genre
- **Régions** : poids des régions, affinités genre-région, convergence des goûts
- **Market Power Index** : poids des 5 composantes réglables, fiche éditeur, export CSV
- **Explorateur de jeux** : profil régional de n'importe quel titre, outliers culturels
- **Qualité des données** : journal de nettoyage et export du jeu propre
- **Synthèse et conclusion** : les six insights clés (recalculés sur les données), difficultés de data wrangling, apport des visualisations, galerie des 24 figures du notebook

L'interface est interactive : un clic sur un jeu (barre, point ou ligne de tableau) ouvre sa fiche, un clic sur une année, un genre, une plateforme ou un éditeur affiche son détail, et les réglages (pondérations du MPI, jeu choisi...) sont conservés d'une page à l'autre. Les calculs sont mis en cache et chaque section réglable se recharge seule, sans recalculer toute la page.

Les filtres de la barre latérale (période, genres, constructeurs, type de plateforme) s'appliquent à toutes les pages d'analyse (la qualité des données et la synthèse portent sur le jeu complet). L'interface nettoie les données brutes au lancement avec le même module que le notebook : un `assert_frame_equal` dans le notebook garantit que les deux donnent un résultat identique.

## Nettoyage en bref

| Problème | Traitement |
|---|---|
| 271 années manquantes | 118 imputées (fiche jumelle ou autres plateformes du même titre, uniquement si elles concordent), 153 supprimées (0,5 % des ventes) |
| 58 éditeurs vides + 203 `Unknown` | une seule modalité `Inconnu` |
| Filiales (*Sony Computer Entertainment Europe*...) | rattachées à leur groupe ; les fusions historiques (SquareSoft, Enix) sont conservées |
| 4 sorties après 2016, 6 jeux datés avant leur console | 5 corrigées, 5 supprimées |
| 149 fiches partielles `(JP sales)`, doublons d'écriture | 114 fiches fusionnées (maximum par région, sans double comptage) |

Résultat : 16 326 jeux, 11 239 titres, 99,3 % du volume de ventes conservé.
