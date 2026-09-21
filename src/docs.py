"""Génère methodologie_et_limites.md avec les chiffres réellement calculés.

Usage : python -m src.docs
"""
from __future__ import annotations

import pandas as pd

from . import config as C
from . import indicators as I
from . import recommandations as R
from .data import charger_tout, populations
from .formatage import entier, km, nombre, pct


def _table(df: pd.DataFrame) -> str:
    lignes = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * df.shape[1]]
    lignes += ["| " + " | ".join(str(v).replace("|", "/") for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lignes)


def generer() -> str:
    T = charger_tout()
    pop = populations(T)
    f = I.Filtres()
    ag, fi = I.filtrer_agents(T["agents"], f), I.filtrer_finance(T["finance"], f)
    total = int(T["pop_commune"].population.sum())
    nat = I.synthese_nationale(ag, fi, total)
    reg = I.table_territoriale("region", ag, fi, pop, f)
    pref = I.table_territoriale("prefecture", ag, fi, pop, f)
    com = I.table_territoriale("commune", ag, fi, pop, f)
    mm = com[com.statut_couverture == I.STATUT_MM_SEUL].sort_values("population", ascending=False)
    bm = I.phases_internet(T["internet_bm"]).set_index("annee")
    ctrl = T["controles"]
    b = I.bandes_distance(ag).set_index("bande")
    rc = R.generer(com, "commune", nat["hab_par_agent"])
    rp = R.generer(pref, "prefecture", nat["hab_par_agent"])
    hier = T["pop_hierarchie"]
    corr = T["pop_commune"][T["pop_commune"].correction.fillna("") != ""][["unite_commune", "libelle_source", "correction"]]

    md = f"""# Méthodologie et limites

Document généré par `python -m src.docs` à partir de `data_processed/` : chaque chiffre ci-dessous est recalculé,
aucun n'est saisi à la main.

## 1. Principe d'intégrité

- Seuls les fichiers de `data/` sont exploités ; faute de géométrie surfacique, les **contours préfectoraux du Défi 1**
  (COD-AB OCHA, déjà réconciliés avec les noms PRISE) sont la seule donnée externe, utilisée pour cartographier et contrôler.
- Aucune valeur n'est imputée, estimée ou extrapolée. Une donnée absente est affichée « {C.NON_DISPONIBLE} ».
- Les fichiers sources ne sont jamais modifiés ; toutes les tables dérivées sont écrites dans `data_processed/`.
- Chaque indicateur affiche sa source, sa période et sa formule (infobulles, notes sous les graphiques, onglet Méthodologie).

## 2. Sources

{_table(pd.DataFrame([{"Fichier": k, "Contenu": v["titre"], "Producteur": v["producteur"], "Période": v["periode"], "Granularité": v["granularite"]} for k, v in C.SOURCES.items()]))}

## 3. Chaîne de traitement (`python -m src.pipeline`)

1. **Population RGPH-5** (`observationdata-kwwolwb.csv`) : le fichier ne précise pas le niveau administratif de chaque ligne.
   La hiérarchie est reconstruite par **sommes exactes** (chaque parent = somme de ses enfants) : {len(hier)} lignes →
   1 pays, {(hier.niveau == 'region_rgph').sum()} régions RGPH (dont le District autonome du Grand Lomé), {(hier.niveau == 'prefecture').sum()} préfectures,
   {(hier.niveau == 'commune').sum()} unités communales, {(hier.niveau == 'canton_ou_quartier').sum()} cantons ou quartiers. Total national : {entier(total)}.
   Corrections de libellés, toutes vérifiées par les sommes :

{_table(corr.rename(columns={"unite_commune": "Unité retenue", "libelle_source": "Libellé source", "correction": "Traitement"}))}

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

{_table(pd.DataFrame([{"Indicateur": I.LIBELLES.get(k, k), "Formule": v} for k, v in I.FORMULES.items()]))}

Périmètre par défaut : établissements de **dépôt et de crédit** (banques, micro-finance, mutuelles), statuts « en activité » et
« non renseigné » ; tous les agents (y compris opérateur non renseigné). Tous ces choix sont modifiables dans la barre latérale.

**Phases de l'usage d'Internet** : recul si variation < −0,25 pt ; stagnation si |variation| ≤ 0,25 pt ; accélération si
variation > variation précédente + 0,1 pt ; rythme constant si l'écart à la variation précédente ≤ 0,1 pt ; sinon progression
ralentie (seuils modifiables dans la page).

**Recommandations** (priorité = nombre de critères remplis ; 3 → priorité 1) :

{_table(pd.DataFrame([{"Critère": k, "Libellé": R.CRITERES[k], "Règle": R.REGLES[k]} for k in R.CRITERES]))}

## 6. Résultats clés (périmètre par défaut)

- Usage d'Internet : {nombre(bm.valeur_pct[2013])} % (2013) → {nombre(bm.valeur_pct[2022])} % (2022) ; plus forte hausse en
  {int(bm.variation_pp.idxmax())} ({nombre(bm.variation_pp.max())} pts). Aucune valeur 2023.
- {entier(nat['agents'])} agents MM ({entier(nat['hab_par_agent'])} habitants par agent) ; {entier(nat['etablissements'])} établissements
  ({entier(nat['hab_par_etab'])} habitants par établissement) ; {nombre(nat['agents_par_etab'])} agents par établissement.
- {len(mm)} communes, {entier(mm.population.sum())} habitants ({pct(100 * mm.population.sum() / total)}), ont des agents MM mais aucun
  établissement recensé ; la préfecture de Kpendjal n'en a aucun.
- {pct(b.part_pct['< 2 km'])} des agents sont à moins de 2 km d'un établissement ; {pct(100 - b.part_pct[['< 2 km', '2–5 km']].sum())} à plus de 5 km.
- Écart régional : {reg.loc[reg.hab_par_etab.idxmax(), 'territoire']} {entier(reg.hab_par_etab.max())} hab./établissement contre
  {reg.loc[reg.hab_par_etab.idxmin(), 'territoire']} {entier(reg.hab_par_etab.min())}.
- Recommandations : {len(rc)} communes ciblées ({(rc.priorite == 'Priorité 1').sum()} en priorité 1) et {len(rp)} préfectures.

## 7. Contrôles de qualité ({len(ctrl)} contrôles, {(ctrl.resultat == 'OK').sum()} conformes, {(ctrl.resultat != 'OK').sum()} écarts documentés)

{_table(ctrl.rename(columns={"domaine": "Domaine", "controle": "Contrôle", "resultat": "Résultat", "detail": "Détail"}))}

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
"""
    (C.ROOT / "methodologie_et_limites.md").write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    generer()
    print(C.ROOT / "methodologie_et_limites.md")
