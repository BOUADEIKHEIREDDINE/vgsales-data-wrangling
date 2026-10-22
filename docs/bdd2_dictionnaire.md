# Dictionnaire des données : deuxième base (notes Metacritic)

## Source

| | |
|---|---|
| Nom | *Video Game Sales with Ratings* |
| Auteur | rush4ratio (Kaggle) |
| Page | https://www.kaggle.com/rush4ratio/video-game-sales-with-ratings |
| Fichier d'origine | `Video_Games_Sales_as_at_22_Dec_2016.csv` |
| Copie téléchargée | https://raw.githubusercontent.com/Yorko/mlcourse.ai/main/data/video_games_sales.csv (copie identique : mêmes 16 719 lignes, mêmes 16 colonnes) |
| Date de téléchargement | 22/10/2026 |
| Date des données | scraping du 22/12/2016 |
| Licence | non précisée par l'auteur (« Unknown » sur la page Kaggle, vérifié le 22/10/2026). Usage limité à ce projet pédagogique, avec la source citée |
| Fichier dans le projet | `BDD_states/bdd2_metacritic.csv` |
| Taille | 16 719 lignes × 16 colonnes |

Construction : l'auteur a repris le scraping de ventes VGChartz (la même source que `bdd1_vgsales.csv`), puis l'a complété par un second scraping de **Metacritic**, qui ajoute les notes de la presse et des joueurs, le développeur et la classification d'âge ESRB. Metacritic ne couvre qu'une partie des plateformes, celles des années 2000 et après, d'où les nombreuses valeurs manquantes sur les colonnes de notes.

## Colonnes

Les valeurs manquantes sont comptées sur le fichier brut, avant nettoyage.

| Colonne | Type brut | Signification | Manquants | Remarques |
|---|---|---|---|---|
| `Name` | texte | Titre du jeu | 2 (0,0 %) | 11 562 titres distincts |
| `Platform` | texte | Code de la plateforme (Wii, PS2, X360...) | 0 | 31 plateformes, mêmes codes que `bdd1_vgsales.csv` |
| `Year_of_Release` | décimal | Année de sortie | 269 (1,6 %) | Équivalent de `Year`. 1980-2020 : 4 dates après 2016 sont incohérentes |
| `Genre` | texte | Genre du jeu | 2 (0,0 %) | 12 genres, mêmes modalités que `bdd1_vgsales.csv` |
| `Publisher` | texte | Éditeur | 54 (0,3 %) | 581 éditeurs |
| `NA_Sales` | décimal | Ventes en Amérique du Nord (millions d'exemplaires) | 0 | Même source que `bdd1_vgsales.csv` (VGChartz) |
| `EU_Sales` | décimal | Ventes en Europe (millions) | 0 | idem |
| `JP_Sales` | décimal | Ventes au Japon (millions) | 0 | idem |
| `Other_Sales` | décimal | Ventes dans le reste du monde (millions) | 0 | idem |
| `Global_Sales` | décimal | Ventes mondiales (millions) | 0 | idem |
| **`Critic_Score`** | décimal | Note de la presse : moyenne Metacritic des critiques professionnelles, **sur 100** | 8 582 (51,3 %) | Entre 13 et 98 |
| **`Critic_Count`** | décimal | Nombre de critiques utilisées pour cette note | 8 582 (51,3 %) | Entre 3 et 113 |
| **`User_Score`** | texte | Note des joueurs inscrits sur Metacritic, **sur 10** | 6 704 (40,1 %) | **2 425 valeurs `"tbd"`** (*to be determined*, pas assez de votes), d'où le type texte. Entre 0 et 9,7 une fois converti |
| **`User_Count`** | décimal | Nombre de joueurs ayant voté | 9 129 (54,6 %) | Entre 4 et 10 665 |
| **`Developer`** | texte | Studio qui a développé le jeu (différent de l'éditeur, qui le finance et le distribue) | 6 623 (39,6 %) | 1 696 studios ; parfois plusieurs studios séparés par une virgule |
| **`Rating`** | texte | Classification d'âge ESRB (organisme nord-américain) | 6 769 (40,5 %) | E 3 991 · T 2 961 · M 1 563 · E10+ 1 420 · EC 8 · K-A 3 · RP 3 · AO 1 |

En **gras** : les colonnes que `bdd1_vgsales.csv` n'a pas. C'est ce qu'apporte la deuxième base.

## Codes ESRB

| Code | Signification |
|---|---|
| EC | *Early Childhood* : petite enfance (3 ans et plus) |
| E | *Everyone* : tout public |
| K-A | *Kids to Adults* : ancien nom de E (jusqu'en 1998) |
| E10+ | *Everyone 10+* : 10 ans et plus |
| T | *Teen* : 13 ans et plus |
| M | *Mature* : 17 ans et plus |
| AO | *Adults Only* : 18 ans et plus |
| RP | *Rating Pending* : classification pas encore attribuée |
