# Prix de la prestation : avant et après l'ajout de la deuxième base

## Hypothèses

| Hypothèse | Valeur retenue |
|---|---|
| Taux journalier moyen (TJM) | **450 € HT** par jour, tarif d'un·e data analyst junior en prestation |
| Journée | 7 heures de travail effectif |
| Mode de calcul | effort d'un professionnel qui connaît les outils, pas le temps passé en cours. Les aléas courants (retours, corrections) sont inclus dans chaque poste |
| Données | sources gratuites (Kaggle) : aucun coût de licence |
| Hors périmètre | hébergement de l'interface, maintenance, mises à jour des données après livraison |
| TVA | 20 % |

## Avant : analyse des ventes seule (`vgsales.csv`)

| Poste | Contenu | Jours | Montant HT |
|---|---|---:|---:|
| Cadrage | compréhension du besoin, lecture du sujet, plan d'analyse | 0,5 | 225 € |
| Audit et nettoyage | diagnostic qualité, 5 familles de problèmes, module `cleaning.py` réutilisable, contrôle de reproductibilité | 2,5 | 1 125 € |
| Analyse exploratoire | statistiques, tendances, genres, plateformes, régions, éditeurs | 2 | 900 € |
| Indicateurs avancés | *Market Power Index* (5 composantes, test de robustesse), divergences régionales | 3 | 1 350 € |
| Visualisation et storytelling | 24 figures commentées, Partie III | 1,5 | 675 € |
| Interface interactive | application Streamlit de 8 pages, filtres, navigation par clic, cache | 4 | 1 800 € |
| Documentation et livrables | README, notebook exécuté, export HTML | 1 | 450 € |
| Recette et suivi | tests, corrections, suivi de projet | 1 | 450 € |
| Restitution | préparation et présentation au client | 0,5 | 225 € |
| **Total** | | **16** | **7 200 € HT** (8 640 € TTC) |

## Après : avec la deuxième base (notes Metacritic)

Le travail de la colonne « Avant » est conservé tel quel. On ajoute :

| Poste | Contenu | Jours | Montant HT |
|---|---|---:|---:|
| Recherche de la source | comparaison des sources possibles, vérification des critères (période, clé commune, apport), licence, dictionnaire des données | 1 | 450 € |
| Nettoyage de la base 2 | module `cleaning_bdd2.py`, valeurs `tbd`, classification ESRB, fausses correspondances (homonymes), journal | 1,5 | 675 € |
| Analyse exploratoire de la base 2 | notes par année, genre, plateforme, éditeur ; presse contre joueurs ; 10 figures commentées | 1,5 | 675 € |
| Jointure et contrôles | normalisation des noms, taux de correspondance, mesure du biais, vérifications manuelles | 1 | 450 € |
| Analyses croisées | notes et ventes, MPI à 6 composantes, sensibilité des régions aux notes | 1,5 | 675 € |
| Intégration à l'interface | nouvelle page, enrichissement de la fiche jeu et des pages existantes, filtres | 2,5 | 1 125 € |
| Documentation | README, documentation de la jointure, conclusion mise à jour | 0,5 | 225 € |
| Recette de non-régression | vérifier que le notebook et l'interface existants fonctionnent toujours | 0,5 | 225 € |
| **Supplément** | | **10** | **4 500 € HT** |
| **Total après** | | **26** | **11 700 € HT** (14 040 € TTC) |

## Synthèse

| | Jours | Prix HT | Prix TTC |
|---|---:|---:|---:|
| Avant (ventes seules) | 16 | 7 200 € | 8 640 € |
| Après (ventes + notes) | 26 | 11 700 € | 14 040 € |
| **Écart** | **+10** | **+4 500 € (+62,5 %)** | **+5 400 €** |

## Justification de l'écart

**Pourquoi la deuxième base coûte-t-elle 62,5 % de plus, et non 100 % ?** Une partie du travail est réutilisée :

- les règles de nettoyage de la Partie I (années, éditeurs, doublons) s'appliquent telles quelles à la deuxième base ;
- le style graphique, la structure du notebook et l'architecture de l'interface existent déjà ;
- le *Market Power Index* est enrichi, pas reconstruit.

**Pourquoi coûte-t-elle quand même 10 jours ?** Parce qu'elle apporte des tâches qui n'existaient pas :

- **chercher et qualifier une source** : il faut vérifier qu'elle est fiable, qu'elle a une clé commune et qu'on a le droit de l'utiliser ;
- **relier deux bases** : normaliser, mesurer le taux de correspondance, contrôler les fausses jointures, mesurer le biais ;
- **croiser** les informations, ce qui est l'apport principal pour le client ;
- **ne rien casser** : chaque ajout doit être testé sur l'existant (recette de non-régression).

## Variante : une source indépendante

Si le client voulait une source vraiment indépendante (API IGDB ou RAWG, données Steam), il faudrait compter **3 à 4 jours de plus**, soit 1 350 à 1 800 € HT. Il faudrait en effet obtenir des clés d'API, collecter les données page par page, et faire une jointure beaucoup plus difficile : noms écrits différemment, plateformes codées autrement, taux de correspondance bien plus faible.
