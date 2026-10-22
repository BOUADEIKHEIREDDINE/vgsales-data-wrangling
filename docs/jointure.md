# Jointure des ventes et des notes Metacritic

Code : `modules/jointure.py`. Analyse détaillée : `bdd2.ipynb`, Partie V.

## Les deux bases

| | Base 1 : ventes | Base 2 : notes |
|---|---|---|
| Fichier brut | `BDD_states/vgsales.csv` | `BDD_states/video_games_ratings.csv` |
| Fichier propre | `BDD_states/vgsales_clean.csv` | `BDD_states/video_games_ratings_clean.csv` |
| Source | VGChartz (scraping fin 2016) | VGChartz + Metacritic (scraping du 22/12/2016), Kaggle rush4ratio |
| Jeux après nettoyage | 16 326 | 16 447 |
| Apport | ventes par région | note presse, note joueurs, studio, classification ESRB |

Les ventes de la base 2 ne sont **pas utilisées**. Elles proviennent d'un autre relevé VGChartz : 75 % des jeux ont exactement les mêmes ventes, mais 186 jeux diffèrent de plus de 0,1 M (*Wii Sports* : 82,74 M contre 82,53 M). `vgsales_clean.csv` reste la seule source de vérité pour les ventes.

## Clé de jointure

**Nom normalisé + plateforme + année.**

| Élément | Pourquoi |
|---|---|
| Nom normalisé | les noms ne sont pas toujours écrits pareil (casse, ponctuation, suffixes) |
| Plateforme | un même jeu n'a pas la même note sur PS3 et sur Wii |
| Année | sépare un jeu de son remake : *Need for Speed: Most Wanted* 2005 et 2012 |

**Règles de normalisation** (fonction `cle_jeu` de `modules/cleaning.py`, la même que pour le nettoyage) :

1. retirer les suffixes de fiches partielles : `(JP sales)`, `(US sales)`, `(Weekly american sales)`... ;
2. passer en minuscules ;
3. supprimer tout ce qui n'est ni une lettre ni un chiffre (ponctuation, espaces, accents).

Exemple : `"WWE SmackDown! vs. RAW 2006"` -> `wwesmackdownvsraw2006`.

Les règles plus poussées citées dans les consignes (article « The », chiffres romains) n'ont pas été nécessaires : les deux bases viennent du même scraping et écrivent les titres de la même façon. Elles deviendraient indispensables avec une source indépendante (IGDB, Steam).

**Type de jointure** : à gauche depuis `vgsales_clean.csv`, avec `validate="one_to_one"`. On garde tous les jeux de l'analyse des ventes, et pandas lève une erreur si un jeu était dupliqué.

## Taux de correspondance

| | Jeux | Part des jeux | Part des ventes |
|---|---:|---:|---:|
| Jeux de `vgsales_clean.csv` | 16 326 | 100 % | 100 % |
| reliés à Metacritic | 16 282 | **99,7 %** | 99,99 % |
| dont avec une note presse | 7 974 | **48,8 %** | **63,0 %** |
| non reliés | 44 | 0,3 % | 0,01 % |
| Jeux Metacritic absents de `vgsales_clean.csv` | 165 | | |

## Vérifications

- **Jeux non reliés (44)** : tous de très petits jeux (0,03 M au plus, 0,56 M au total), probablement retirés ou renommés sur VGChartz entre les deux relevés.
- **Jeux présents seulement dans Metacritic (165)** : 158 sont sortis en 2016. Ce sont des sorties de fin 2016 (*Battlefield 1*, *Titanfall 2*...) que `vgsales.csv`, extrait plus tôt, ne contenait pas encore.
- **Échantillon tiré au hasard** : éditeur, studio et titre cohérents ; aucune fausse jointure.
- **Homonymes** : les remakes sont séparés par l'année. Lorsque la source avait attribué la même note à l'original et au remake, la note a été retirée au nettoyage (6 lignes).

## Limites

1. **Biais de couverture** : 30 % des jeux les moins vendus ont une note, contre 65 % des plus vendus. Les conclusions sur les notes décrivent surtout les jeux visibles.
2. **Biais temporel** : 1 % des jeux des années 1980 sont notés, 61 % de ceux des années 2000. Les notes ne permettent pas d'étudier le marché avant 2000.
3. **Biais géographique** : Metacritic regroupe des critiques occidentales. Beaucoup de jeux japonais n'ont pas de note, et les éditeurs japonais sont mal couverts. Pour le MPI, 26 éditeurs sur 73 reçoivent une note neutre (la médiane).
4. **Corrélation et causalité** : la jointure permet de mesurer un lien entre notes et ventes, pas de dire que la note cause les ventes.
