"""Chargement des tables de data_processed/ (sans dépendance Streamlit)."""
from __future__ import annotations

import json

import pandas as pd

from . import config as C

TABLES = {
    "agents": "agents_mobile_money.csv",
    "finance": "etablissements_financiers.csv",
    "pop_region": "population_region.csv",
    "pop_prefecture": "population_prefecture.csv",
    "pop_commune": "population_commune.csv",
    "pop_hierarchie": "population_hierarchie.csv",
    "internet_bm": "series_internet_bm.csv",
    "telecom": "series_telecom.csv",
    "controles": "controles_qualite.csv",
    "dictionnaire": "dictionnaire_donnees.csv",
    "journal": "journal_qualite.csv",
    "schema": "schema_champs.csv",
}
GEO = {"prefectures": "geo_prefectures.geojson", "regions": "geo_regions.geojson", "pays": "geo_pays.geojson"}


class DonneesManquantes(FileNotFoundError):
    pass


def lire_table(cle: str) -> pd.DataFrame:
    chemin = C.PROCESSED_DIR / TABLES[cle]
    if not chemin.exists():
        raise DonneesManquantes(f"Fichier absent : data_processed/{TABLES[cle]} — lancez `python -m src.pipeline`.")
    return pd.read_csv(chemin, encoding="utf-8", keep_default_na=True)


def lire_geo(cle: str) -> dict | None:
    chemin = C.PROCESSED_DIR / GEO[cle]
    if not chemin.exists():
        return None
    return json.loads(chemin.read_text(encoding="utf-8"))


def populations(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {"region": tables["pop_region"], "prefecture": tables["pop_prefecture"], "commune": tables["pop_commune"]}


def charger_tout() -> dict[str, pd.DataFrame]:
    return {k: lire_table(k) for k in TABLES}
