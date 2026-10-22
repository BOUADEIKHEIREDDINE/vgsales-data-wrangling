# Ventes mondiales de jeux vidéo (1980-2016)

Projet final de Data Wrangling : nettoyage, analyse exploratoire, indicateurs avancés et interface interactive, à partir du fichier `vgsales.csv` (16 598 jeux, ventes en millions d'exemplaires, source VGChartz), complété par une deuxième source, les notes Metacritic (`video_games_ratings.csv`, 16 719 lignes).

## Contenu

| Élément | Rôle |
|---|---|
| `projet_final.ipynb` | **Livrable principal.** Notebook exécuté : Partie I (nettoyage), Partie II (EDA, Market Power Index, divergences régionales), Partie III (storytelling), conclusion |
| `projet_final.html` | Le même notebook, lisible dans un navigateur sans Jupyter |
| `bdd2.ipynb` (+ `bdd2.html`) | **Deuxième source.** Partie IV (nettoyage et EDA des notes Metacritic), Partie V (jointure avec les ventes, notes et ventes, MPI avec la qualité, régions) |
| `app/dashboard.py` | Interface web interactive (Streamlit), 9 pages |
| `modules/` | Code partagé : `cleaning.py` (règles de nettoyage), `indicators.py` (MPI, divergences), `config.py`, `viz.py`, `cleaning_bdd2.py` (nettoyage des notes), `jointure.py` (jointure et MPI à 6 composantes) |
| `BDD_states/` | `vgsales.csv` (brut), `vgsales_clean.csv` (propre), `market_power_index.csv`, `divergence_regionale.csv`, `video_games_ratings.csv` (brut, base 2), `video_games_ratings_clean.csv`, `vgsales_ratings_joint.csv` (ventes + notes) |
| `figures/` | Les graphiques des notebooks en PNG : 01 à 24 (`projet_final.ipynb`), 25 à 38 (`bdd2.ipynb`) |
| `docs/` | `dictionnaire_bdd2.md` (dictionnaire des données de la base 2), `jointure.md` (méthode et limites de la jointure), `prix_prestation.md` (chiffrage avant / après) |
| `presentation/` | Les diapos de la soutenance (style Pac-Man, en PPTX et en PDF) : `presentation_complete` (les deux parties dans un seul fichier), `BDD1_vgsales_pacman` (partie ventes), `BDD2_metacritic_pacman` (partie notes Metacritic) |
| `consignes.md` | Organisation de l'équipe : répartition du travail, branches, PR |
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

`bdd2.ipynb` s'exécute de la même façon, indépendamment du premier. Il régénère `video_games_ratings_clean.csv`, `vgsales_ratings_joint.csv` et les figures 25 à 38.

## Lancer l'interface

```bash
python run_app.py
```

puis ouvrir http://localhost:8501. Les pages :

- **Vue d'ensemble** : chiffres clés, ventes par constructeur, top 10, messages clés
- **Tendances et plateformes** : jeux et ventes par année, cycle de vie des consoles, classement
- **Genres** : fréquence contre ventes, évolution, leaders par genre
- **Régions** : poids des régions, affinités genre-région, convergence des goûts
- **Market Power Index** : poids des 5 composantes réglables (et, en option, une 6e : la qualité perçue), fiche éditeur, export CSV
- **Explorateur de jeux** : profil régional de n'importe quel titre, outliers culturels
- **Notes Metacritic** (deuxième source) : taux de jointure, notes et ventes, presse contre joueurs, sensibilité des régions aux notes
- **Qualité des données** : journaux de nettoyage des deux bases, bilan de la jointure, export des jeux propres
- **Synthèse et conclusion** : les six insights clés et les trois apports de la deuxième source (recalculés sur les données), difficultés de data wrangling, apport des visualisations, galerie des figures des deux notebooks

Le thème reprend le style arcade des diapos (fond noir, murs bleus, police pixel *Press Start 2P* sous licence OFL) : voir `app/theme.py`. Les figures du notebook gardent leur palette claire.

La deuxième source enrichit aussi les pages existantes : la fiche d'un jeu affiche ses notes, son studio et sa classification d'âge ; le classement des plateformes affiche leur note moyenne ; la page Genres propose les notes par genre.

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

## Deuxième source : les notes Metacritic

*Video Game Sales with Ratings* (Kaggle, rush4ratio, scraping du 22/12/2016) ajoute à chaque jeu sa **note presse** (/100), sa **note joueurs** (/10), le nombre d'avis, le **studio** et la **classification d'âge ESRB**. Détail des colonnes : `docs/dictionnaire_bdd2.md`.

| Problème | Traitement |
|---|---|
| 2 425 notes joueurs `tbd` | valeurs manquantes, colonne convertie en nombre |
| 51 % de notes presse manquantes | non imputées : Metacritic ne couvre que les jeux récents (biais documenté) |
| Années, éditeurs, doublons | mêmes règles que la base 1 (118 années imputées, 114 fiches fusionnées) |
| Remakes notés comme l'original | note retirée (6 lignes) |
| Notes sur peu d'avis | signalées (`Note_Presse_Fiable`, `Note_Joueurs_Fiable`) |

**Jointure** sur nom normalisé + plateforme + année : 99,7 % des jeux reliés, mais 49 % seulement ont une note presse (63 % des ventes). Méthode, vérifications et limites : `docs/jointure.md`.

**Prix de la prestation** : 7 200 € HT pour l'analyse des ventes seule, 11 700 € HT avec la deuxième base (TJM 450 €). Détail : `docs/prix_prestation.md`.

## Présentation

Les diapos sont dans `presentation/`. Pour la soutenance, projeter `presentation_complete.pptx` : partie 1 (ventes VGChartz), puis partie 2 (notes Metacritic), puis une seule démo de l'interface à la fin, qui montre les deux bases ensemble. Les fichiers `BDD1_…` et `BDD2_…` contiennent chaque partie seule.

Les animations (Pac-Man qui avance sur la barre de progression, transitions) ne marchent que dans PowerPoint. Les PDF sont des versions statiques, à utiliser pour lire les diapos ou en secours.
