# Dictionnaire de données

Généré automatiquement par `src/audit.py` (lancé par `python -m src.pipeline`). Les fichiers de `data/` sont lus sans modification.

## 1. Fichiers sources

| fichier | contenu | producteur | période | granularité |
|---|---|---|---|---|
| file-agents-mobile-money-19-12-2024-16-55-32.csv | Agents mobile money géolocalisés | Géoportail national du Togo — campagne de collecte PRISE | Collecte PRISE 2021/2022 (catalogue du géoportail, audit Défi 1) ; extraction du 19/12/2024 | Point GPS (région, préfecture, commune, canton déclarés) |
| agents-mobile-money.csv | Schéma de la couche agents mobile money (46 champs décrits) | Géoportail national du Togo | Sans objet (métadonnées) | Sans objet |
| file-finance-etablissements-08-01-2025-17-49-30.csv | Établissements financiers géolocalisés (banques, IMF, mutuelles, assurances) | Géoportail national du Togo (couche finance_etablissements_banque) | Période de collecte non indiquée dans le fichier ; extraction du 08/01/2025 | Point GPS (région, préfecture, commune, canton déclarés) |
| finance-etablissements.csv | Schéma de la couche établissements financiers (107 champs décrits) | Géoportail national du Togo | Sans objet (métadonnées) | Sans objet |
| individus-utilisant-internet-de-la-population-.csv | Individus utilisant Internet (% de la population) | Banque mondiale — World Development Indicators (IT.NET.USER.ZS, donnée UIT) | 1960–2023 (valeurs renseignées jusqu'en 2022) | National |
| observationdata-cxnvmoc.csv | Abonnés Internet par technologie et opérateur, taux de pénétration | Export « observationdata » d'un portail de données — producteur non indiqué dans le fichier | 2013–2019 | National (certaines séries par opérateur) |
| observationdata-mesqyx.csv | Marché des télécommunications : abonnés, télédensité, CA, investissement, parts de marché | Export « observationdata » d'un portail de données — producteur non indiqué dans le fichier | 2013–2019 | National (parts de marché par opérateur) |
| observationdata-kwwolwb.csv | Population résidente par découpage administratif (RGPH-5) | INSEED — RGPH-5 (export « observationdata ») | 2022 (recensement) | Pays, région, préfecture, commune, canton/quartier |

## 2. Colonnes des fichiers de données

### `file-agents-mobile-money-19-12-2024-16-55-32.csv`

*Agents mobile money géolocalisés* — période : Collecte PRISE 2021/2022 (catalogue du géoportail, audit Défi 1) ; extraction du 19/12/2024 — granularité : Point GPS (région, préfecture, commune, canton déclarés)

| colonne | type | non_nuls | taux_manquant_pct | taux_non_informatif_pct | valeurs_distinctes | min | max | exemples |
|---|---|---|---|---|---|---|---|---|
| FID | texte | 19788 | 0.0 | 0.0 | 19788 |  |  | _mview_tel_agents_mobile_money.fid-7111a / _mview_tel_agents_mobile_money.fid-7111a / _mview_tel_agents_mobile_money.fid-7111a |
| region_nom_bdd | texte | 19788 | 0.0 | 0.0 | 5 |  |  | Maritime / Plateaux / Kara |
| prefecture_nom_bdd | texte | 19788 | 0.0 | 0.0 | 39 |  |  | Golfe / Kozah / Tchaoudjo |
| commune_nom_bdd | texte | 19788 | 0.0 | 0.0 | 117 |  |  | Kozah 1 / Tchaoudjo 1 / Golfe 1 |
| canton_nom_bdd | texte | 19788 | 0.0 | 0.0 | 372 |  |  | Commune De Kara / Bè-Est / Aflao-Gakli |
| operateur | texte | 19788 | 0.0 | 6.81 | 4 |  |  | Moov, Togocom / Togocom / Nsp |
| geometry | géométrie (WKT Point) | 19788 | 0.0 | 0.0 | 19788 |  |  | POINT (1.2144986445140882 6.145976688064 / POINT (0.3032083333333333 10.99665166666 / POINT (0.3600592001272428 10.71756508836 |

### `file-finance-etablissements-08-01-2025-17-49-30.csv`

*Établissements financiers géolocalisés (banques, IMF, mutuelles, assurances)* — période : Période de collecte non indiquée dans le fichier ; extraction du 08/01/2025 — granularité : Point GPS (région, préfecture, commune, canton déclarés)

| colonne | type | non_nuls | taux_manquant_pct | taux_non_informatif_pct | valeurs_distinctes | min | max | exemples |
|---|---|---|---|---|---|---|---|---|
| FID | texte | 738 | 0.0 | 0.0 | 738 |  |  | _mview_finance_etablissements_banque.fid / _mview_finance_etablissements_banque.fid / _mview_finance_etablissements_banque.fid |
| region_nom_bdd | texte | 738 | 0.0 | 0.0 | 5 |  |  | Maritime / Plateaux / Kara |
| prefecture_nom_bdd | texte | 738 | 0.0 | 0.0 | 38 |  |  | Golfe / Agoè-Nyivé / Zio |
| commune_nom_bdd | texte | 738 | 0.0 | 0.0 | 95 |  |  | Golfe 5 / Golfe 1 / Agoè-Nyivé 1 |
| canton_nom_bdd | texte | 738 | 0.0 | 0.0 | 130 |  |  | Aflao-Gakli / Bè-Est / Agoè-Nyivé |
| nom_localite | texte | 738 | 0.0 | 3.39 | 462 |  |  | N/a / AKODESSEWA / Adidogomé |
| etab_nom | texte | 738 | 0.0 | 0.0 | 730 |  |  | COOPEC la Fructueuse / Assilassime Solidarité / Mutuelle Nevaeme |
| etab_adresse | texte | 738 | 0.0 | 37.67 | 415 |  |  | Néant / Nsp / BP 359 |
| etab_jour | texte | 738 | 0.0 | 0.41 | 52 |  |  | {Lundi,Mardi,Mercredi,Jeudi,Vendredi,Sam / {Lundi,Mardi,Mercredi,Jeudi,Vendredi} / {Samedi,Vendredi,Jeudi,Mercredi,Mardi,Lu |
| activite_statut | texte | 738 | 0.0 | 8.27 | 14 |  |  | Utilisé / Néant / Autre |
| activite_categorie | texte | 738 | 0.0 | 0.0 | 5 |  |  | Micro-Finance / Banque / Assurance |
| toilette_type | texte | 738 | 0.0 | 37.26 | 20 |  |  | N/a / {WCs} / {Latrines a eau} |
| geometry | géométrie (WKT Point) | 738 | 0.0 | 0.0 | 738 |  |  | POINT (0.63340629671594 6.91447997875899 / POINT (1.1654270638510162 6.203541360604 / POINT (0.025253169999999 11.0961158) |

### `individus-utilisant-internet-de-la-population-.csv`

*Individus utilisant Internet (% de la population)* — période : 1960–2023 — granularité : National

| colonne | type | non_nuls | taux_manquant_pct | taux_non_informatif_pct | valeurs_distinctes | min | max | exemples |
|---|---|---|---|---|---|---|---|---|
| indicator | texte | 64 | 0.0 | 0.0 | 1 |  |  | Individuals using the Internet (% of pop |
| country | texte | 64 | 0.0 | 0.0 | 1 |  |  | Togo |
| countryiso3code | texte | 64 | 0.0 | 0.0 | 1 |  |  | TGO |
| date | entier | 64 | 0.0 | 0.0 | 64 | 1960 | 2023 | 2023 / 2022 / 2021 |
| value | décimal | 51 | 20.31 | 0.0 | 28 | 0.0 | 37.6212 | 0.0 / 37.6212 / 29.0237 |
| unit | décimal | 0 | 100.0 | 0.0 | 0 | nan | nan |  |
| obs_status | décimal | 0 | 100.0 | 0.0 | 0 | nan | nan |  |
| decimal | entier | 64 | 0.0 | 0.0 | 1 | 0 | 0 | 0 |

### `observationdata-cxnvmoc.csv`

*Abonnés Internet par technologie et opérateur, taux de pénétration* — période : 2013–2019 — granularité : National (certaines séries par opérateur)

| colonne | type | non_nuls | taux_manquant_pct | taux_non_informatif_pct | valeurs_distinctes | min | max | exemples |
|---|---|---|---|---|---|---|---|---|
| indicateur | texte | 160 | 0.0 | 0.0 | 25 |  |  | T abonnés Internet Fixe et Mobile (Toute / T abonnés Internet haut débit Fixe et Mo / T abonnés Internet mobiles (Toutes techn |
| Unit | texte | 160 | 0.0 | 0.0 | 1 |  |  | Nombre |
| Date | entier | 160 | 0.0 | 0.0 | 7 | 2013 | 2019 | 2013 / 2014 / 2015 |
| Value | décimal | 160 | 0.0 | 0.0 | 128 | 0.0 | 3686211.0 | 0.0 / 431869.0 / 210448.0 |

### `observationdata-mesqyx.csv`

*Marché des télécommunications : abonnés, télédensité, CA, investissement, parts de marché* — période : 2013–2019 — granularité : National (parts de marché par opérateur)

| colonne | type | non_nuls | taux_manquant_pct | taux_non_informatif_pct | valeurs_distinctes | min | max | exemples |
|---|---|---|---|---|---|---|---|---|
| indicateur | texte | 70 | 0.0 | 0.0 | 10 |  |  | Le nombre total d'abonnés fixe et mobile / Le nombre total d'abonnées mobiles GSM / Le nombre total d'abonnés fixe |
| Unit | texte | 70 | 0.0 | 0.0 | 3 |  |  | % / Nombre / Francs CFA |
| Date | entier | 70 | 0.0 | 0.0 | 7 | 2013 | 2019 | 2013 / 2014 / 2015 |
| Value | décimal | 70 | 0.0 | 0.0 | 70 | 0.47 | 33234000000000.0 | 3778401.0 / 4272018.0 / 4710010.0 |

### `observationdata-kwwolwb.csv`

*Population résidente par découpage administratif (RGPH-5)* — période : 2022–2022 — granularité : Pays, région, préfecture, commune, canton/quartier

| colonne | type | non_nuls | taux_manquant_pct | taux_non_informatif_pct | valeurs_distinctes | min | max | exemples |
|---|---|---|---|---|---|---|---|---|
| indicateur | texte | 759 | 0.0 | 0.0 | 1 |  |  | Population résidente par découpage admin |
| découpage-administratif | texte | 759 | 0.0 | 0.0 | 745 |  |  | ATSANVE / CINKASSE / SOTOUBOUA |
| sexe | texte | 759 | 0.0 | 0.0 | 1 |  |  | Total |
| Unit | texte | 759 | 0.0 | 0.0 | 1 |  |  | Nombre |
| Date | entier | 759 | 0.0 | 0.0 | 1 | 2022 | 2022 | 2022 |
| Value | entier | 759 | 0.0 | 0.0 | 743 | 132 | 8095498 | 16044 / 20414 / 4303 |

## 3. Champs décrits dans les schémas mais absents des fichiers fournis

Les fichiers `agents-mobile-money.csv` et `finance-etablissements.csv` décrivent la structure complète des couches. Les extractions fournies n'en contiennent qu'une partie : toute analyse reposant sur les champs absents est impossible.

### `file-agents-mobile-money-19-12-2024-16-55-32.csv` — 6 champs présents / 46 décrits

Présents : `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `operateur`, `geometry`

Absents : `id`, `canton_id_bdd`, `etab_id_collecte`, `agent_id`, `agent_genre`, `agent_nom`, `agent_annee`, `agent_tel`, `metier`, `metier_spec`, `telephone_type`, `service`, `id_moov`, `date_moov`, `flooz`, `flooz_id`, `flooz_date`, `id_togocom`, `vente_point_num`, `date_togocom`, `tmoney`, `tmoney_id`, `tmoney_date`, `transfert_international`, `services_autre`, `lieu`, `batiment`, `agent_nbr`, `patron`, `patron_type`, `patron_entreprise`, `patron_personne`, `patron_genre`, `patron_tel`, `transfert_nbr`, `pb`, `solution`, `remarque`, `date_collecte`, `date_mise_a_jour_collecte`

### `file-finance-etablissements-08-01-2025-17-49-30.csv` — 12 champs présents / 107 décrits

Présents : `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `nom_localite`, `etab_nom`, `etab_adresse`, `etab_jour`, `activite_statut`, `activite_categorie`, `toilette_type`, `geometry`

Absents : `id`, `canton_id_bdd`, `etab_id_collecte`, `etab_heure`, `interlocuteur_presence`, `interlocuteur_responsable`, `interlocuteur_fonction`, `interlocuteur_nom_prenom`, `interlocuteur_genre`, `interlocuteur_tel`, `responsable_nom_prenom`, `responsable_genre`, `responsable_fonction`, `responsable_tel`, `responsable_mail`, `responsable_annee`, `activite_categorie_banque`, `activite_description`, `org_creation_date`, `org_nom`, `org_type`, `org_type_autre`, `org_ministere_tutelle`, `org_numero_prive`, `org_fodes`, `org_fodes_num`, `org_numero_autre`, `org_type2`, `org_type2_international`, `org_qg`, `personnel_nbr`, `personnel_femme_nbr`, `personnel_homme_nbr`, `personnel_admin_nbr`, `personnel_comm_nbr`, `reception`, `guichet_nbr`, `client_parti`, `client_prive`, `eau_acces`, `eau_source`, `eau_source_autre`, `eau_pression`, `eau_debit`, `eau_acces_temps`, `eau_qualite`, `lavage`, `lavage_type`, `lavage_type_autre`, `elec_acces`, `elec_source`, `elec_qualite`, `elec_acces_temps`, `internet`, `internet_type`, `internet_type_autre`, `internet_type_fournisseur`, `couverture`, `couverture_type`, `couverture_nom`, `ordinateur_portable_nbr`, `ordinateur_portable_fonctionnel_nbr`, `ordinateur_poste_nbr`, `ordinateur_poste_fonctionnel_nbr`, `equipement_specifique`, `toilette`, `toilette_separation`, `toilette_raccordage`, `toilette_raccordage_non`, `toilette_fosse`, `wc_nbr`, `latrine_nbr`, `latrine_seche_nbr`, `pissotiere_nbr`, `douche_nbr`, `lampadaire`, `lampadaire_nbr`, `lampadaire_solaire_nbr`, `lampadaire_reseau_nbr`, `lampadaire_art_nbr`, `rampe_handicape`, `batiment_nbr`, `vehicule_4_roue_nbr`, `vehicule_3_roue_nbr`, `vehicule_2_roue_nbr`, `gab_nbr`, `gab_fct_nbr`, `cloture`, `cloture_type`, `cloture_materiau`, `pb`, `solution_potentielle`, `commentaire`, `date_collecte`, `date_mise_a_jour_collecte`

## 4. Journal de qualité des données observées

| fichier | lignes | doublons | couverture_temporelle | couverture_geographique | valeurs_non_informatives | limites |
|---|---|---|---|---|---|---|
| file-agents-mobile-money-19-12-2024-16-55-32.csv | 19788 | 0 | Collecte PRISE 2021/2022 (catalogue du géoportail, audit Défi 1) ; extraction du 19/12/2024 | 5 régions · 39 préfectures · 117 communes · 372 cantons | opérateur « Nsp » : 1348 agents (6.8%) | 40 champs du schéma absents sur 46 (date de collecte, genre, services, volumes de transferts…) ; un agent = un point de service, pas un volume d'activité ; présence déclarée à la date de collecte |
| file-finance-etablissements-08-01-2025-17-49-30.csv | 738 | 0 | Période de collecte non indiquée dans le fichier ; extraction du 08/01/2025 | 5 régions · 38 préfectures · 95 communes · 130 cantons | statut ambigu (Néant, Nsp, N/a, Autre, Location) : 63 ; adresse « Néant/Nsp » : 278 | 95 champs du schéma absents sur 107 (nombre de guichets, GAB, clients, personnel, date de création…) ; un enregistrement = un établissement, pas un nombre de guichets ; catégorie telle que déclarée |
| individus-utilisant-internet-de-la-population-.csv | 64 | 0 | 1960–2022 renseignées ; 13 années vides (dont 2023) | National | — | Aucune ventilation territoriale, par sexe ou par âge ; méthodologie UIT (estimations possibles) |
| observationdata-cxnvmoc.csv | 160 | 0 | 2013–2019 (séries partielles : 4G Moov 2013–2017, EV-DO 2013–2017, Illiconet 2013–2014, LS point à point 2013) | National | — | Producteur non indiqué ; unité « Nombre » pour des taux en % ; opérateur non précisé pour les offres fixes ; pas de série après 2019 |
| observationdata-mesqyx.csv | 70 | 0 | 2013–2019 | National | — | ARPU incohérent avec l'unité (exclu) ; périmètre du CA et de l'investissement non précisé ; CA et investissement non ventilés par opérateur |
| observationdata-kwwolwb.csv | 759 | 0 | 2022 (RGPH-5) | Pays · 6 régions RGPH (dont DAGL) · 39 préfectures · 116 unités communales · 597 cantons/quartiers | — | Niveau non indiqué dans le fichier (reconstruit par les sommes) ; Danyi 1 et 2 fusionnées ; 3 libellés de communes erronés ; cantons non appariables de façon fiable aux cantons PRISE (orthographes, quartiers du Grand Lomé) |

## 5. Tables produites (`data_processed/`)

| table | lignes | colonnes |
|---|---|---|
| `population_hierarchie.csv` | 759 | ligne_source, niveau, libelle_source, population, parent, region_bdd, prefecture_bdd, commune_bdd, correction |
| `population_region.csv` | 5 | region, population, regions_rgph |
| `population_prefecture.csv` | 39 | region, prefecture, population, libelle_source, region_rgph |
| `population_commune.csv` | 116 | region, prefecture, unite_commune, communes_bdd, population, libelle_source, correction |
| `commune_vers_unite.csv` | 117 | commune, unite_commune |
| `series_internet_bm.csv` | 64 | annee, valeur_pct, indicateur, source, observation |
| `series_telecom.csv` | 230 | indicateur_source, unite_source, annee, valeur, fichier, famille, libelle, groupe, operateur_source, technologie, unite, statut_qualite |
| `agents_mobile_money.csv` | 19788 | agent_id, region, prefecture, commune, canton, operateur_source, sert_togocom, sert_moov, lon, lat, classe_operateur, unite_commune, prefecture_geom, coherence_geo … |
| `etablissements_financiers.csv` | 738 | etab_id, nom, localite, region, prefecture, commune, canton, categorie, categorie_source, statut_source, statut_groupe, jours_ouverture, nb_jours_ouverture, ouvert_samedi … |

Géométries : `geo_prefectures.geojson`, `geo_regions.geojson`, `geo_pays.geojson` (contours COD-AB OCHA réconciliés au Défi 1, simplifiés à ~250 m pour l'affichage). Contrôles : `controles_qualite.csv`.
