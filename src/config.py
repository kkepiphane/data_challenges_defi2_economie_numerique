"""Chemins, sources et constantes partagés par le pipeline, l'application et le rapport."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = ROOT / "data_processed"
ASSETS_DIR = ROOT / "assets"
OUTPUTS_DIR = ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"

# Contours préfectoraux du Défi 1 (COD-AB OCHA, noms déjà réconciliés avec la base PRISE).
# Seule donnée externe au dossier data/ : les fichiers fournis ne contiennent aucune géométrie surfacique.
DEFI1_GEOMETRY_CANDIDATES = [
    ROOT.parent / "defi1" / "data" / "processed" / "prefectures.gpkg",
    ROOT / "data_defi1" / "prefectures.gpkg",
]
DEFI1_AUDIT_SOURCES = "defi1/reports/audit_sources.md"

# --------------------------------------------------------------------------------------
# Fichiers sources (dossier data/, lecture seule)
# --------------------------------------------------------------------------------------
SRC_AGENTS = "file-agents-mobile-money-19-12-2024-16-55-32.csv"
SRC_AGENTS_SCHEMA = "agents-mobile-money.csv"
SRC_FINANCE = "file-finance-etablissements-08-01-2025-17-49-30.csv"
SRC_FINANCE_SCHEMA = "finance-etablissements.csv"
SRC_INTERNET_BM = "individus-utilisant-internet-de-la-population-.csv"
SRC_TELECOM_INTERNET = "observationdata-cxnvmoc.csv"
SRC_TELECOM_MARCHE = "observationdata-mesqyx.csv"
SRC_POPULATION = "observationdata-kwwolwb.csv"

SOURCES = {
    SRC_AGENTS: {
        "titre": "Agents mobile money géolocalisés",
        "producteur": "Géoportail national du Togo — campagne de collecte PRISE",
        "periode": "Collecte PRISE 2021/2022 (catalogue du géoportail, audit Défi 1) ; extraction du 19/12/2024",
        "granularite": "Point GPS (région, préfecture, commune, canton déclarés)",
    },
    SRC_AGENTS_SCHEMA: {
        "titre": "Schéma de la couche agents mobile money (46 champs décrits)",
        "producteur": "Géoportail national du Togo",
        "periode": "Sans objet (métadonnées)",
        "granularite": "Sans objet",
    },
    SRC_FINANCE: {
        "titre": "Établissements financiers géolocalisés (banques, IMF, mutuelles, assurances)",
        "producteur": "Géoportail national du Togo (couche finance_etablissements_banque)",
        "periode": "Période de collecte non indiquée dans le fichier ; extraction du 08/01/2025",
        "granularite": "Point GPS (région, préfecture, commune, canton déclarés)",
    },
    SRC_FINANCE_SCHEMA: {
        "titre": "Schéma de la couche établissements financiers (107 champs décrits)",
        "producteur": "Géoportail national du Togo",
        "periode": "Sans objet (métadonnées)",
        "granularite": "Sans objet",
    },
    SRC_INTERNET_BM: {
        "titre": "Individus utilisant Internet (% de la population)",
        "producteur": "Banque mondiale — World Development Indicators (IT.NET.USER.ZS, donnée UIT)",
        "periode": "1960–2023 (valeurs renseignées jusqu'en 2022)",
        "granularite": "National",
    },
    SRC_TELECOM_INTERNET: {
        "titre": "Abonnés Internet par technologie et opérateur, taux de pénétration",
        "producteur": "Export « observationdata » d'un portail de données — producteur non indiqué dans le fichier",
        "periode": "2013–2019",
        "granularite": "National (certaines séries par opérateur)",
    },
    SRC_TELECOM_MARCHE: {
        "titre": "Marché des télécommunications : abonnés, télédensité, CA, investissement, parts de marché",
        "producteur": "Export « observationdata » d'un portail de données — producteur non indiqué dans le fichier",
        "periode": "2013–2019",
        "granularite": "National (parts de marché par opérateur)",
    },
    SRC_POPULATION: {
        "titre": "Population résidente par découpage administratif (RGPH-5)",
        "producteur": "INSEED — RGPH-5 (export « observationdata »)",
        "periode": "2022 (recensement)",
        "granularite": "Pays, région, préfecture, commune, canton/quartier",
    },
}

POPULATION_SOURCE_LABEL = "RGPH-5 (INSEED), 2022"
AGENTS_SOURCE_LABEL = "Géoportail PRISE 2021/2022"
FINANCE_SOURCE_LABEL = "Géoportail, extraction 01/2025"
BM_SOURCE_LABEL = "Banque mondiale (WDI/UIT)"
TELECOM_SOURCE_LABEL = "Séries sectorielles 2013–2019"

# --------------------------------------------------------------------------------------
# Nomenclatures
# --------------------------------------------------------------------------------------
REGIONS = ["Savanes", "Kara", "Centrale", "Plateaux", "Maritime"]  # ordre nord → sud

# Régions du RGPH-5 → régions de la base PRISE (5 régions ; le Grand Lomé y est rattaché à Maritime)
RGPH_REGION_TO_BDD = {
    "SAVANES": "Savanes",
    "KARA": "Kara",
    "CENTRALE": "Centrale",
    "PLATEAUX": "Plateaux",
    "MARITIME": "Maritime",
    "DAGL": "Maritime",
}
# Libellés préfectoraux du RGPH-5 non appariables par simple normalisation
RGPH_PREFECTURE_ALIASES = {"TOTOALAVE": "AVE"}

FIN_CATEGORIES = ["Banque", "Micro-finance", "Mutuelle", "Assurance"]
FIN_CATEGORY_MAP = {
    "Banque": "Banque",
    "Micro-Finance": "Micro-finance",
    "Micro-Finace": "Micro-finance",
    "Mutuelle": "Mutuelle",
    "Assurance": "Assurance",
}
# Par défaut : établissements de dépôt et de crédit (accès au compte, dépôt, retrait, crédit)
FIN_CATEGORIES_DEFAULT = ["Banque", "Micro-finance", "Mutuelle"]

STATUT_ACTIF = "En activité"
STATUT_NR = "Statut non renseigné ou ambigu"
STATUT_NOP = "Déclaré non opérationnel"
STATUT_GROUPES = [STATUT_ACTIF, STATUT_NR, STATUT_NOP]
STATUT_MAP = {
    "Utilisé": STATUT_ACTIF,
    "Utilise": STATUT_ACTIF,
    "Néant": STATUT_NR,
    "Nsp": STATUT_NR,
    "N/a": STATUT_NR,
    "Autre": STATUT_NR,
    "{autre}": STATUT_NR,
    "Location": STATUT_NR,
    "Fermé": STATUT_NOP,
    "En construction": STATUT_NOP,
    "Inacheve": STATUT_NOP,
    "Abandonné": STATUT_NOP,
    "En réfection": STATUT_NOP,
    "Sans Local": STATUT_NOP,
}
STATUT_DEFAULT = [STATUT_ACTIF, STATUT_NR]

OPERATEURS = ["Togocom", "Moov"]
OP_NR = "Non renseigné"
OP_CLASSES = ["Moov + Togocom", "Togocom seul", "Moov seul", OP_NR]

# Codes courts des colonnes de distance pré-calculées (catégorie × statut)
CAT_CODES = {"Banque": "BQ", "Micro-finance": "MF", "Mutuelle": "MU", "Assurance": "AS"}
STATUT_CODES = {STATUT_ACTIF: "ACT", STATUT_NR: "NR", STATUT_NOP: "NOP"}


def dist_col(categorie: str, statut: str) -> str:
    return f"dist_km_{CAT_CODES[categorie]}_{STATUT_CODES[statut]}"


# Seuils d'éloignement (km, distance à vol d'oiseau)
DIST_BANDES = [0, 2, 5, 10, 20, float("inf")]
DIST_LABELS = ["< 2 km", "2–5 km", "5–10 km", "10–20 km", "≥ 20 km"]
SEUIL_ELOIGNEMENT_KM = 5

ANNEE_MIN, ANNEE_MAX = 1990, 2023
PERIODE_DEFAUT = (2000, 2023)

NON_DISPONIBLE = "Donnée non disponible dans les sources fournies"
