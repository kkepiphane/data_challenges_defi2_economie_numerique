# Méthodologie et limites

Document généré par `python -m src.docs` à partir de `data_processed/` : chaque chiffre ci-dessous est recalculé,
aucun n'est saisi à la main.

## 1. Principe d'intégrité

- Seuls les fichiers de `data/` sont exploités ; faute de géométrie surfacique, les **contours préfectoraux du Défi 1**
  (COD-AB OCHA, déjà réconciliés avec les noms PRISE) sont la seule donnée externe, utilisée pour cartographier et contrôler.
- Aucune valeur n'est imputée, estimée ou extrapolée. Une donnée absente est affichée « Donnée non disponible dans les sources fournies ».
- Les fichiers sources ne sont jamais modifiés ; toutes les tables dérivées sont écrites dans `data_processed/`.
- Chaque indicateur affiche sa source, sa période et sa formule (infobulles, notes sous les graphiques, onglet Méthodologie).

## 2. Sources

| Fichier | Contenu | Producteur | Période | Granularité |
|---|---|---|---|---|
| file-agents-mobile-money-19-12-2024-16-55-32.csv | Agents mobile money géolocalisés | Géoportail national du Togo — campagne de collecte PRISE | Collecte PRISE 2021/2022 (catalogue du géoportail, audit Défi 1) ; extraction du 19/12/2024 | Point GPS (région, préfecture, commune, canton déclarés) |
| agents-mobile-money.csv | Schéma de la couche agents mobile money (46 champs décrits) | Géoportail national du Togo | Sans objet (métadonnées) | Sans objet |
| file-finance-etablissements-08-01-2025-17-49-30.csv | Établissements financiers géolocalisés (banques, IMF, mutuelles, assurances) | Géoportail national du Togo (couche finance_etablissements_banque) | Période de collecte non indiquée dans le fichier ; extraction du 08/01/2025 | Point GPS (région, préfecture, commune, canton déclarés) |
| finance-etablissements.csv | Schéma de la couche établissements financiers (107 champs décrits) | Géoportail national du Togo | Sans objet (métadonnées) | Sans objet |
| individus-utilisant-internet-de-la-population-.csv | Individus utilisant Internet (% de la population) | Banque mondiale — World Development Indicators (IT.NET.USER.ZS, donnée UIT) | 1960–2023 (valeurs renseignées jusqu'en 2022) | National |
| observationdata-cxnvmoc.csv | Abonnés Internet par technologie et opérateur, taux de pénétration | Export « observationdata » d'un portail de données — producteur non indiqué dans le fichier | 2013–2019 | National (certaines séries par opérateur) |
| observationdata-mesqyx.csv | Marché des télécommunications : abonnés, télédensité, CA, investissement, parts de marché | Export « observationdata » d'un portail de données — producteur non indiqué dans le fichier | 2013–2019 | National (parts de marché par opérateur) |
| observationdata-kwwolwb.csv | Population résidente par découpage administratif (RGPH-5) | INSEED — RGPH-5 (export « observationdata ») | 2022 (recensement) | Pays, région, préfecture, commune, canton/quartier |

## 3. Chaîne de traitement (`python -m src.pipeline`)

1. **Population RGPH-5** (`observationdata-kwwolwb.csv`) : le fichier ne précise pas le niveau administratif de chaque ligne.
   La hiérarchie est reconstruite par **sommes exactes** (chaque parent = somme de ses enfants) : 759 lignes →
   1 pays, 6 régions RGPH (dont le District autonome du Grand Lomé), 39 préfectures,
   116 unités communales, 597 cantons ou quartiers. Total national : 8 095 498.
   Corrections de libellés, toutes vérifiées par les sommes :

| Unité retenue | Libellé source | Traitement |
|---|---|---|
| Danyi 1 + Danyi 2 | DANYI 1+DANYI 2 | unité fusionnée dans la source (« DANYI 1+DANYI 2 ») : population commune non séparable |
| Amou 3 | AMOU 2 | libellé source « AMOU 2 » en position 3 → Amou 3 (somme des cantons vérifiée) |
| Est-Mono 3 | EST-MONO 1 | libellé source « EST-MONO 1 » en position 3 → Est-Mono 3 (somme des cantons vérifiée) |

2. **Agents mobile money** : coordonnées extraites du WKT ; opérateurs éclatés (« Moov, Togocom » = agent servant les deux ;
   « Nsp » = non renseigné) ; rattachement à l'unité de population de sa commune.
3. **Établissements financiers** : catégorie harmonisée (« Micro-Finace » → micro-finance) ; statut regroupé en trois classes
   (en activité ; non renseigné ou ambigu ; déclaré non opérationnel) ; jours d'ouverture normalisés (casse, ordre).
4. **Distances** : pour chaque agent, distance du grand cercle (BallTree haversine) à l'établissement le plus proche, calculée pour
   chacune des 12 combinaisons catégorie × statut ; l'application retient le minimum sur la sélection de l'utilisateur.
5. **Cohérence spatiale** : point dans polygone sur les contours du Défi 1 (contrôle seulement : l'attribut déclaré fait foi).
6. **Séries télécoms** : libellés clarifiés, unité corrigée (taux en % déclarés « Nombre »), cohérences internes vérifiées.
7. **Audit** : dictionnaire de données, champs de schéma absents, journal de qualité (`data_dictionary.md`, `data_processed/*.csv`).

## 4. Jointures

| Jointure | Statut | Justification |
|---|---|---|
| Points ↔ population, régions et préfectures | Réalisée (5/5, 39/39) | Noms normalisés, alias « TOTOAL AVE » → Avé ; DAGL rattaché à Maritime comme dans PRISE |
| Points ↔ population, communes | Réalisée (117 communes → 116 unités) | Rang de la commune dans sa préfecture, contrôlé par le numéro du libellé |
| Points ↔ population, cantons | **Impossible de manière fiable** | Orthographes divergentes, cantons RGPH absents de PRISE, quartiers du Grand Lomé ≠ cantons PRISE |
| Agents ↔ établissements | Réalisée (distance GPS) | Plus proche voisin |
| Séries télécoms ↔ agents | Correspondance nominative seulement | Togo Cellulaire et Togo Telecom → Togocom ; Atlantique Telecom → Moov ; périodes disjointes, aucun ratio croisé |
| Usage d'Internet ↔ territoires | Impossible | Série nationale uniquement |

## 5. Définitions et formules

| Indicateur | Formule |
|---|---|
| Habitants par agent MM | Population RGPH-5 2022 ÷ nombre d'agents mobile money recensés |
| Habitants par établissement financier | Population RGPH-5 2022 ÷ nombre d'établissements financiers recensés (catégories et statuts sélectionnés) |
| Agents MM pour 10 000 hab. | Agents mobile money × 10 000 ÷ population |
| Établissements pour 100 000 hab. | Établissements financiers × 100 000 ÷ population |
| Agents MM par établissement financier | Agents mobile money ÷ établissements financiers (même territoire) |
| Distance médiane agent → établissement (km) | Médiane, sur les agents du territoire, de la distance à vol d'oiseau au plus proche établissement sélectionné |
| Agents à plus de 5 km d'un établissement (%) | Part des agents situés à plus de 5 km à vol d'oiseau de tout établissement sélectionné |
| Rang moyen de sous-desserte (0–1) | Moyenne des rangs centiles (0 = mieux desservi, 1 = moins bien desservi) de 4 indicateurs, poids égaux : habitants par agent, habitants par établissement, distance médiane, part d'agents éloignés |
| hhi | Indice de Herfindahl-Hirschman = somme des carrés des parts de marché (en %) ; 10 000 = monopole |
| variation_pp | Valeur de l'année − valeur de l'année précédente (points de pourcentage) |
| tcam | Taux de croissance annuel moyen = (valeur finale ÷ valeur initiale)^(1 / nombre d'années) − 1 |

Périmètre par défaut : établissements de **dépôt et de crédit** (banques, micro-finance, mutuelles), statuts « en activité » et
« non renseigné » ; tous les agents (y compris opérateur non renseigné). Tous ces choix sont modifiables dans la barre latérale.

**Phases de l'usage d'Internet** : recul si variation < −0,25 pt ; stagnation si |variation| ≤ 0,25 pt ; accélération si
variation > variation précédente + 0,1 pt ; rythme constant si l'écart à la variation précédente ≤ 0,1 pt ; sinon progression
ralentie (seuils modifiables dans la page).

**Recommandations** (priorité = nombre de critères remplis ; 3 → priorité 1) :

| Critère | Libellé | Règle |
|---|---|---|
| C1 | Aucun établissement de dépôt/crédit observé | établissements (catégories et statuts sélectionnés) = 0 et agents MM > 0 |
| C2 | Plus de 2× la référence nationale d'habitants par agent MM | habitants par agent > 2 × (population nationale ÷ agents nationaux, mêmes filtres) |
| C3 | Distance médiane agent → établissement > 10 km | médiane des distances à vol d'oiseau des agents au plus proche établissement > 10 km |
| C4 | Établissement(s) présent(s) mais ≥ 50 % des agents à > 5 km | établissements > 0 et part des agents à plus de 5 km ≥ 50 % |

## 6. Résultats clés (périmètre par défaut)

- Usage d'Internet : 4,5 % (2013) → 37,6 % (2022) ; plus forte hausse en
  2020 (8,3 pts). Aucune valeur 2023.
- 19 788 agents MM (409 habitants par agent) ; 656 établissements
  (12 341 habitants par établissement) ; 30,2 agents par établissement.
- 22 communes, 759 599 habitants (9,4 %), ont des agents MM mais aucun
  établissement recensé ; la préfecture de Kpendjal n'en a aucun.
- 74,0 % des agents sont à moins de 2 km d'un établissement ; 15,2 % à plus de 5 km.
- Écart régional : Savanes 18 746 hab./établissement contre
  Maritime 9 930.
- Recommandations : 52 communes ciblées (11 en priorité 1) et 14 préfectures.

## 7. Contrôles de qualité (47 contrôles, 45 conformes, 2 écarts documentés)

| Domaine | Contrôle | Résultat | Détail |
|---|---|---|---|
| Agents MM | Hiérarchie région → préfecture → commune sans conflit | OK | 5 régions · 39 préfectures · 117 communes · 372 cantons |
| Établissements | Hiérarchie région → préfecture → commune sans conflit | OK | 5 régions · 38 préfectures · 95 communes · 130 cantons |
| Population | Indicateur, sexe, unité et année uniques | OK | Population résidente par découpage administratif et par sexe · sexe=Total · 2022 |
| Population | Aucune valeur manquante | OK | 759 lignes |
| Population | Hiérarchie reconstruite sans reste (somme des enfants = parent à chaque nœud) | OK | 759 nœuds |
| Population | Total national = 8 095 498 (RGPH-5, identique au livret INSEED du Défi 1) | OK | 8 095 498 |
| Population | 39 préfectures appariées aux noms de la base PRISE | OK | 39/39 |
| Population | Rattachement préfecture → région identique RGPH-5 / PRISE | OK | Grand Lomé (DAGL) rattaché à Maritime comme dans la base PRISE |
| Population | 117 communes PRISE couvertes par 116 unités de population | OK | 117 communes · 116 unités (Danyi 1 + Danyi 2 fusionnées) |
| Population | Somme préfectorale = somme communale = total national | OK | 8 095 498 |
| Population | Correction de libellé — Danyi 1 + Danyi 2 | OK | unité fusionnée dans la source (« DANYI 1+DANYI 2 ») : population commune non séparable |
| Population | Correction de libellé — Amou 3 | OK | libellé source « AMOU 2 » en position 3 → Amou 3 (somme des cantons vérifiée) |
| Population | Correction de libellé — Est-Mono 3 | OK | libellé source « EST-MONO 1 » en position 3 → Est-Mono 3 (somme des cantons vérifiée) |
| Agents MM | Aucune valeur manquante | OK | 19788 lignes × 7 colonnes |
| Agents MM | Identifiants FID uniques | OK | nan |
| Agents MM | Aucune géométrie dupliquée | OK | nan |
| Agents MM | Valeurs d'opérateur reconnues (Moov, Togocom, Nsp) | OK | Moov, Togocom : 12 649 · Togocom : 4 773 · Nsp : 1 348 · Moov : 1 018 |
| Agents MM | Tous les agents rattachés à une unité de population communale | OK | 19788/19788 |
| Établissements | Aucune valeur manquante | OK | 738 lignes × 13 colonnes |
| Établissements | Identifiants FID uniques | OK | nan |
| Établissements | Aucune géométrie dupliquée | OK | nan |
| Établissements | Catégories reconnues ; « Micro-Finace » fusionnée avec « Micro-Finance » | OK | Micro-Finance : 412 · Banque : 247 · Assurance : 69 · Mutuelle : 9 · Micro-Finace : 1 |
| Établissements | Statuts d'activité regroupés en 3 classes | OK | Utilisé : 658 · Néant : 50 · Autre : 6 · Fermé : 5 · En construction : 4 · Nsp : 3 · Location : 2 · Inacheve : 2 · Utilise : 2 · Abandonné : 2 · {autre} : 1 · En réfection : 1 · Sans Local : 1 · N/a : 1 |
| Établissements | Jours d'ouverture exploitables | OK | 735/738 renseignés (casse harmonisée) |
| Établissements | Homonymes dans une même commune (signalés, conservés : coordonnées distinctes) | OK | 2 enregistrements |
| Établissements | Tous les établissements rattachés à une unité de population communale | OK | 738/738 |
| Géométrie | Contours préfectoraux (COD-AB OCHA, réconciliés au Défi 1) : 39 unités, noms PRISE | OK | prefectures.gpkg |
| Géométrie | Agents MM : points situés dans un contour préfectoral | OK | 19748/19788 (99.80%) ; les autres sont en limite de frontière |
| Géométrie | Agents MM : préfecture géométrique = préfecture déclarée | OK | 19431/19748 (98.39%) ; l'attribut déclaré fait foi pour les agrégations |
| Géométrie | Établissements : points situés dans un contour préfectoral | OK | 738/738 (100.00%) ; les autres sont en limite de frontière |
| Géométrie | Établissements : préfecture géométrique = préfecture déclarée | OK | 732/738 (99.19%) ; l'attribut déclaré fait foi pour les agrégations |
| Géométrie | Superficie totale (projection équivalente LAEA) | OK | 57 242 km² |
| Distances | Distance au plus proche établissement calculée (12 combinaisons catégorie × statut) | OK | BallTree haversine, rayon terrestre 6 371 km ; établissements hors Togo non couverts par les données |
| Internet (BM) | Pays et indicateur uniques | OK | Togo · Individuals using the Internet (% of population) |
| Internet (BM) | Valeurs comprises entre 0 et 100 % | OK | dernière année renseignée : 2022 (37.6 %) |
| Internet (BM) | Années sans valeur (non imputées) | OK | 1961, 1962, 1963, 1964, 1966, 1967, 1968, 1969, 1971, 1972, 1973, 1974, 2023 |
| Télécoms | Tous les indicateurs sources documentés | OK | 35 indicateurs |
| Télécoms | Aucun doublon indicateur × année | OK | nan |
| Télécoms | Aucune valeur manquante | OK | 230 observations, 2013–2019 |
| Télécoms | Parts de marché Togocom + Moov = 100 % | OK | 7 années |
| Télécoms | Abonnés fixe + mobile = abonnés GSM + abonnés fixe | OK | 7 années |
| Télécoms | Internet mobile total = Togocom + Moov | OK | 7 années |
| Télécoms | Internet mobile haut débit = 3G + 4G des deux opérateurs | OK | 7 années ; 4G Moov absente de la source en 2018–2019 (égalité vérifiée sans elle, aucune valeur imputée) |
| Télécoms | Total Togocom = 2G + 3G + 4G | OK | 7 années |
| Télécoms | Total Moov = 2G + 3G (+ 4G si renseignée) | OK | 7 années |
| Télécoms | ARPU cohérent avec l'unité déclarée (FCFA) | ÉCART | ARPU 2019 = 2.56e+13 FCFA > CA 2019 = 1.85e+11 FCFA → série exclue des graphiques |
| Télécoms | Unité des taux de pénétration Internet | ÉCART | unité source « Nombre » alors que le libellé indique (%) : valeurs conservées, unité affichée % |

Tests applicatifs : `python tests/test_app.py` exécute les 7 pages pour 12 combinaisons de filtres extrêmes
(sélection vide, préfecture sans établissement, commune fusionnée, période hors séries…) — 84 exécutions sans erreur.

## 8. Limites et analyses impossibles

| Analyse | Raison |
|---|---|
| Évolution du nombre de points de service | Aucune date de collecte individuelle ; une seule extraction par couche |
| Guichets, GAB, clients par établissement | Champs absents du fichier fourni (13 champs présents sur 107 décrits) |
| Transactions, services offerts, genre des agents | Champs absents (7 champs présents sur 46 décrits) |
| Détention de comptes (bancaires, mobile money) | Aucune donnée d'enquête ou de comptes |
| Usage d'Internet par territoire, sexe, âge | Série nationale uniquement |
| Couverture 2G/3G/4G/fibre par territoire | Aucune donnée de couverture dans les sources |
| CA et investissement par opérateur ; ARPU | Séries nationales ; ARPU d'unité incohérente (exclu) |
| Séries télécoms après 2019 ; 4G Moov 2018–2019 | Absentes des fichiers fournis |
| Ratios par habitant au niveau canton | Population cantonale non appariable de façon fiable |
| Choroplèthes communales | Aucun contour communal disponible |
| Temps d'accès réel | Pas de réseau routier : distances à vol d'oiseau ; établissements hors frontière non recensés |
| Effets causaux | Aucune variable explicative ni dispositif d'identification |

**Absence dans les données ≠ absence réelle du service** : « aucun établissement observé » signifie qu'aucun établissement n'est
recensé dans le fichier fourni ; cette distinction n'est pas démontrable avec les données disponibles.
