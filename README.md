# Inclusion numérique et financière par le mobile money au Togo

Tableau de bord Streamlit et rapport PowerPoint construits **exclusivement** à partir des données fournies
(`data/`) et, faute de géométrie surfacique, des contours préfectoraux du Défi 1. Aucune valeur n'est
imputée, estimée ou extrapolée : une donnée absente est affichée « Donnée non disponible dans les sources fournies ».

## Constats principaux (périmètre par défaut)

| Constat | Valeur | Source |
|---|---|---|
| Individus utilisant Internet | 4,5 % (2013) → 37,6 % (2022) | Banque mondiale (WDI/UIT) |
| Agents mobile money | 19 788, soit 409 habitants par agent | Géoportail PRISE 2021/22 · RGPH-5 2022 |
| Établissements de dépôt/crédit | 656, soit 12 341 habitants par établissement | Géoportail (extraction 01/2025) |
| Communes avec agents MM mais aucun établissement recensé | 22 communes, 759 599 habitants (9,4 %) | Calcul, mêmes sources |
| Agents à plus de 5 km d'un établissement | 15,2 % | Distance à vol d'oiseau (haversine) |
| Marché mobile 2019 | Togocom 51,4 % · Moov 48,6 % (HHI 5 004) | Séries sectorielles 2013–2019 |

## Installation et lancement

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux : source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

L'application ne lit que `data_processed/` (déjà fourni). Pour tout reconstruire depuis les sources :

```bash
python -m src.pipeline    # data/ → data_processed/ : nettoyage, jointures, distances, 47 contrôles, dictionnaire
python -m src.docs        # methodologie_et_limites.md (chiffres recalculés)
python -m src.rapport     # outputs/rapport_inclusion_numerique_togo.pptx + figures
python tests/test_app.py  # 7 pages × 17 scénarios de filtres, niveaux et vues (119 exécutions)
```

Le pipeline cherche les contours préfectoraux dans `../defi1/data/processed/prefectures.gpkg`, puis dans
`data_defi1/prefectures.gpkg` (copie incluse dans l'archive). Sans eux, les cartes choroplèthes sont remplacées
par un message explicite ; les cartes de points restent disponibles.

## Pages du tableau de bord

| Page | Contenu |
|---|---|
| Vue d'ensemble | KPI avec année et source, carte des habitants par établissement, constats calculés, tableau régional |
| Usage d'Internet | Série 1990–2022, variations annuelles, phases (seuils réglables), épisodes, comparaison avec la pénétration par abonnements |
| Télécommunications | Parts de marché et HHI, 2G/3G/4G par opérateur, Internet fixe et fibre, CA et investissement, explorateur d'indicateurs |
| Services financiers | Carte multicouche (agents, établissements, population), vues réseau / opérateurs / densité, répartitions, recherche |
| Inclusion territoriale | Ratios par habitant (région, préfecture, commune), carte, classement, matrice de chaleur, éloignement, cantons |
| Recommandations | Territoires ciblés par règles explicites (C1–C4), actions et impacts qualitatifs, export CSV |
| Méthodologie | Sources, formules, jointures, 47 contrôles, journal de qualité, dictionnaire, champs absents, analyses impossibles |

**Filtres globaux persistants** (barre latérale) : période, région → préfecture → commune (en cascade), opérateurs,
agents à opérateur non renseigné, catégories et statuts d'établissements, bouton « Réinitialiser ». Chaque page
rappelle sous son titre les filtres modifiés. Tous les tableaux sont téléchargeables en CSV.

## Identité visuelle

Interface sobre : fond blanc, encre noire, un vert institutionnel (#1E6B4F) pour les éléments actifs et des teintes
vert pâle pour les cartes, sélecteurs et la barre latérale. Dans les graphiques, la couleur est réservée à l'information
(trois teintes désaturées validées pour le daltonisme, rouge pour les alertes). Police Public Sans. Armoiries de la
République togolaise en en-tête ; précisions méthodologiques dans les infobulles « i ».

## Structure

```
app.py                  point d'entrée (navigation, filtres globaux)
pages/                  7 pages
src/
  config.py             chemins, sources, nomenclatures
  pipeline.py           préparation reproductible (data/ → data_processed/)
  audit.py              dictionnaire de données et journal de qualité
  indicators.py         filtres, tables territoriales, rangs, phases (fonctions pures)
  recommandations.py    règles C1–C4
  charts.py · ui.py     graphiques Plotly et composants d'interface
  figures.py · rapport.py   cartes matplotlib et deck python-pptx
  docs.py               methodologie_et_limites.md
assets/                 feuille de style, armoiries du Togo, logo, favicon
data/                   sources (lecture seule)
data_processed/         tables nettoyées, géométries, contrôles
data_defi1/             contours préfectoraux du Défi 1 (archive uniquement)
tests/                  test de fumée Streamlit
```

## Documents

- `data_dictionary.md` : dictionnaire automatique (fichiers, colonnes, types, manquants, périodes, granularité, champs absents).
- `methodologie_et_limites.md` : méthode, jointures, formules, contrôles, limites et analyses impossibles.
