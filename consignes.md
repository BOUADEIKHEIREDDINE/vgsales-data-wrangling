# Consignes pour l'équipe

Dépôt GitHub : **https://github.com/BOUADEIKHEIREDDINE/vgsales-data-wrangling**

Présentation : **vendredi 23 octobre 2026**

Le client veut qu'on **ajoute une deuxième base de données** à l'analyse. Ce document dit ce qui est déjà fait et ce qu'il reste à faire.

---

## 1. Ce qui est déjà fait (Kheireddine)

Tout le travail sur `bdd1_vgsales.csv` (16 598 jeux, source VGChartz, 1980-2016) est terminé et poussé sur `main`.

| Élément | Contenu |
|---|---|
| `bdd1_vgsales.ipynb` (+ `bdd1_vgsales.html`) | Livrable principal, exécuté de bout en bout : Partie I (nettoyage), Partie II (EDA, Market Power Index, divergences régionales), Partie III (storytelling), conclusion |
| `modules/bdd1_cleaning.py` | Toutes les règles de nettoyage (utilisées par le notebook **et** par l'interface) |
| `modules/bdd1_indicators.py` | Calcul du Market Power Index (5 composantes) et du score de divergence régionale |
| `modules/config.py` | Chemins, régions, table des plateformes (constructeur, génération...), couleurs |
| `modules/viz.py` | Style commun des graphiques du notebook |
| `app/` | Interface Streamlit de 8 pages, interactive (clic sur un jeu, une année, un genre...). Lancement : `python run_app.py` |
| `BDD_states/` | `bdd1_vgsales.csv` (brut), `bdd1_vgsales_clean.csv`, `bdd1_market_power_index.csv`, `bdd1_divergence_regionale.csv` |
| `figures/` | Les 24 graphiques du notebook en PNG (réutilisables pour les diapos) |
| `README.md` | Installation, lancement, résumé du nettoyage |

Résultat du nettoyage : 16 326 jeux, 11 239 titres, 99,3 % des ventes conservées (détail dans le README et dans la page « Qualité des données » de l'interface).

---

## 2. Ce qu'il reste à faire

### 2.1 Trouver la deuxième base de données

C'est à vous de chercher et de trouver la base dont la prof a parlé. Critères pour qu'elle soit utilisable :

- elle porte sur les **jeux vidéo**, sur une période qui recoupe **1980-2016** ;
- elle a une **clé commune** avec la nôtre, au minimum le **nom du jeu** (`Name`), idéalement aussi la **plateforme** (`Platform`) et/ou l'**année** ;
- elle apporte une **information nouvelle** (notes, prix, développeur, classification, ventes de consoles, ventes numériques...) ;
- source citable (Kaggle, site officiel, API publique), avec la licence ou les conditions d'usage notées.

Pistes pour chercher : Kaggle, data.world, les API publiques (IGDB, RAWG), les jeux de données Metacritic ou Steam.

À noter dans la doc : le lien, la date de téléchargement, le nombre de lignes et de colonnes, et ce que veut dire chaque colonne.

### 2.2 Refaire les mêmes analyses sur la nouvelle base

Suivre **la même structure que le sujet** (voir `Projet_Etudiant.docx`), dans la mesure où les colonnes le permettent :

1. **Nettoyage** : structure, valeurs manquantes, types, doublons, préparation. Chaque décision doit être justifiée et chiffrée (combien de lignes touchées, quelle part du total), comme dans la Partie I du notebook.
2. **EDA** : statistiques descriptives, top 10, tendances par année, genres, plateformes, éditeurs.
3. **Visualisations** : chaque graphique a un titre, des axes nommés et **une interprétation écrite en dessous**.

### 2.3 Relier la nouvelle base à la base actuelle (si possible)

- Faire la jointure sur `Name` + `Platform` (+ `Year` si besoin). Les noms ne sont jamais écrits pareil d'une source à l'autre : normaliser avant de joindre (minuscules, ponctuation, espaces, « The », chiffres romains...).
- **Mesurer le taux de correspondance** : combien de jeux de `bdd1_vgsales_clean.csv` retrouvent un partenaire, et quelle part des ventes cela représente. Si les jeux reliés sont surtout des gros titres, le signaler (biais).
- Vérifier quelques correspondances à la main pour éviter les fausses jointures (remakes, rééditions, homonymes).
- Ensuite, **croiser** : la nouvelle information explique-t-elle les ventes ? Change-t-elle le classement des éditeurs (MPI) ? Les différences régionales ?
- Si la jointure n'est pas possible, l'expliquer et comparer les deux bases au niveau agrégé (par année, genre, plateforme).

### 2.4 Le prix avant et après l'ajout de la deuxième base

Chiffrer la prestation pour le client :

- **Avant** : le travail sur `bdd1_vgsales.csv` seul (nettoyage, EDA, indicateurs, notebook, interface).
- **Après** : le même travail avec la deuxième base (recherche de la source, nettoyage, jointure, nouvelles analyses, mise à jour de l'interface et de la doc).
- Détailler par poste (jours ou heures × taux journalier), dire quelles hypothèses on prend et justifier l'écart entre les deux prix.

### 2.5 La documentation

- Mettre à jour `README.md` : nouvelle source, nouveaux fichiers, nouvelles pages de l'interface.
- Ajouter un **dictionnaire des données** pour la deuxième base (colonne, type, signification, valeurs manquantes).
- Documenter la jointure : clé utilisée, règles de normalisation, taux de correspondance, limites.
- Compléter la **conclusion** du notebook : nouveaux insights, nouvelles difficultés de data wrangling.

### 2.6 Ajouter le travail sur GitHub sans casser l'existant

Règles à respecter :

- **Ne jamais travailler directement sur `main`.** Créer une branche :
  ```bash
  git pull origin main
  git checkout -b bdd2-<votre-prenom>
  ```
- **Ne pas écraser les fichiers existants.** On ajoute des fichiers, on ne remplace pas :
  - données : `BDD_states/<nom_bdd2>.csv` (brut) et `BDD_states/<nom_bdd2>_clean.csv`
  - nettoyage : un nouveau module `modules/bdd2_cleaning.py` (ne pas modifier les règles de `bdd1_cleaning.py`)
  - chemins : ajouter les nouvelles constantes **à la suite** dans `modules/config.py`
  - notebook : une **nouvelle partie** à la fin de `bdd1_vgsales.ipynb` (ou un notebook séparé `bdd2_metacritic.ipynb`), sans modifier les cellules existantes
  - figures : continuer la numérotation (`25_...png`, `26_...png`)
- **Vérifier que rien n'est cassé avant de pousser** : le notebook tourne en entier (*Run All*) et `python run_app.py` démarre sans erreur, sur toutes les pages.
- Pousser la branche et ouvrir une **Pull Request** vers `main` ; quelqu'un d'autre la relit avant le merge.
  ```bash
  git push origin bdd2-<votre-prenom>
  ```
- Ne pas committer `.venv/`, ni de fichiers temporaires, ni de fichiers de plus de 50 Mo (GitHub les refuse).

### 2.7 Intégrer la deuxième base à l'interface (de manière intelligente)

Ne pas se contenter d'une page isolée avec un tableau brut. L'idée est que la nouvelle information **enrichisse** ce qui existe :

- **Une nouvelle page** dans `app/dashboard.py` (dictionnaire `pages`), par exemple « Deuxième source » : présentation de la base, qualité, taux de jointure, principaux graphiques croisés.
- **Enrichir les pages existantes** là où c'est pertinent :
  - la **fiche d'un jeu** (`profil_jeu` dans `app/views.py`) affiche les nouvelles informations quand le jeu a été relié ;
  - les pages Genres / Plateformes / Éditeurs ajoutent l'indicateur nouveau en option (case à cocher ou onglet) ;
  - la page « Qualité des données » ajoute le journal de nettoyage de la deuxième base ;
  - la page « Synthèse et conclusion » ajoute les nouveaux insights.
- Les **filtres de la barre latérale** (période, genres, constructeurs) doivent aussi s'appliquer aux données de la nouvelle base.
- Charger les données dans `app/donnees.py` avec `@st.cache_data`, comme pour les données actuelles, pour que l'interface reste fluide.
- Les graphiques vont dans `app/charts.py` (même style : fonction `habiller`).

### 2.8 Les diapos pour la présentation de vendredi

Plan proposé (environ 12-15 diapos) :

1. Titre, équipe
2. Contexte et demande du client
3. Les deux sources de données (origine, taille, période, ce que chacune apporte)
4. Nettoyage : les problèmes rencontrés et comment on les a traités (chiffres clés)
5. La jointure entre les deux bases : méthode et taux de correspondance
6. 4 à 6 diapos d'insights : un message par diapo, un graphique, une phrase de conclusion (reprendre les figures de `figures/` et les nouvelles)
7. Market Power Index : avant / après la deuxième base
8. Démo de l'interface (courte, préparer le parcours à l'avance)
9. Prix de la prestation avant / après
10. Limites et difficultés de data wrangling
11. Conclusion et recommandations au client

Répéter au moins une fois en entier avant vendredi, et avoir une version PDF au cas où l'ordinateur ou le réseau lâche.

---

## 3. Répartition

| Tâche | Responsable | Échéance |
|---|---|---|
| Trouver la 2e base (2.1) | | |
| Nettoyage + analyses 2e base (2.2) | | |
| Jointure et analyses croisées (2.3) | | |
| Prix avant / après (2.4) | | |
| Documentation (2.5) | | |
| Intégration interface (2.7) | | |
| Diapos (2.8) | | jeudi 22 octobre (veille) |
