"""Dictionnaire de données et journal de qualité, générés automatiquement à partir des fichiers."""
from __future__ import annotations

import pandas as pd

from . import config as C

NON_INFORMATIF = {"nsp", "n/a", "néant", "neant", "{autre}", "autre"}
DONNEES = [C.SRC_AGENTS, C.SRC_FINANCE, C.SRC_INTERNET_BM, C.SRC_TELECOM_INTERNET, C.SRC_TELECOM_MARCHE, C.SRC_POPULATION]
SCHEMAS = {C.SRC_AGENTS: C.SRC_AGENTS_SCHEMA, C.SRC_FINANCE: C.SRC_FINANCE_SCHEMA}


def _type(s: pd.Series) -> str:
    if s.dtype.kind in "iu":
        return "entier"
    if s.dtype.kind == "f":
        return "entier (avec manquants)" if s.dropna().mod(1).eq(0).all() and s.notna().any() else "décimal"
    if s.dtype.kind == "b":
        return "booléen"
    v = s.dropna().astype(str)
    if len(v) and v.str.startswith("POINT").all():
        return "géométrie (WKT Point)"
    return "texte"


def _exemples(s: pd.Series, n: int = 3) -> str:
    vc = s.dropna().astype(str).str.strip().value_counts()
    return " | ".join(x[:40] for x in vc.index[:n])


def _periode(nom: str, df: pd.DataFrame) -> str:
    for col in ["date", "Date"]:
        if col in df:
            v = pd.to_numeric(df[col], errors="coerce").dropna()
            return f"{int(v.min())}–{int(v.max())}"
    return C.SOURCES[nom]["periode"]


def dictionnaire_sources() -> pd.DataFrame:
    lignes = []
    for nom in DONNEES:
        df = pd.read_csv(C.DATA_DIR / nom, encoding="utf-8")
        for col in df.columns:
            s = df[col]
            txt = s.dropna().astype(str).str.strip().str.lower()
            lignes.append({
                "fichier": nom, "colonne": col, "type": _type(s),
                "lignes": len(s), "non_nuls": int(s.notna().sum()),
                "taux_manquant_pct": round(100 * s.isna().mean(), 2),
                "taux_non_informatif_pct": round(100 * txt.isin(NON_INFORMATIF).sum() / len(s), 2) if s.dtype == object else 0.0,
                "valeurs_distinctes": int(s.nunique()),
                "min": s.min() if s.dtype.kind in "iuf" else "", "max": s.max() if s.dtype.kind in "iuf" else "",
                "exemples": _exemples(s),
                "periode": _periode(nom, df), "granularite": C.SOURCES[nom]["granularite"],
            })
    return pd.DataFrame(lignes)


def champs_schema() -> pd.DataFrame:
    lignes = []
    for donnees, schema in SCHEMAS.items():
        sc = pd.read_csv(C.DATA_DIR / schema, encoding="utf-8")
        presents = set(pd.read_csv(C.DATA_DIR / donnees, nrows=1).columns)
        for _, r in sc.iterrows():
            lignes.append({"fichier_donnees": donnees, "fichier_schema": schema, "no": r["No."],
                           "champ": r["Nom du champ"], "question": "" if pd.isna(r["Question"]) else r["Question"],
                           "type": r["Type du champ"], "present_dans_les_donnees": r["Nom du champ"] in presents})
    return pd.DataFrame(lignes)


def journal_qualite(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ag, fi = tables["agents_mobile_money"], tables["etablissements_financiers"]
    bm, tel = tables["series_internet_bm"], tables["series_telecom"]
    hier = tables["population_hierarchie"]
    sch = champs_schema()

    def absents(f):
        s = sch[sch.fichier_donnees == f]
        return f"{(~s.present_dans_les_donnees).sum()} champs du schéma absents sur {len(s)}"

    return pd.DataFrame([
        {"fichier": C.SRC_AGENTS, "lignes": len(ag), "doublons": 0,
         "couverture_temporelle": C.SOURCES[C.SRC_AGENTS]["periode"],
         "couverture_geographique": f"5 régions · {ag.prefecture.nunique()} préfectures · {ag.commune.nunique()} communes · {ag.canton.nunique()} cantons",
         "valeurs_non_informatives": f"opérateur « Nsp » : {(ag.operateur_source == 'Nsp').sum()} agents ({(ag.operateur_source == 'Nsp').mean():.1%})",
         "limites": f"{absents(C.SRC_AGENTS)} (date de collecte, genre, services, volumes de transferts…) ; "
                    "un agent = un point de service, pas un volume d'activité ; présence déclarée à la date de collecte"},
        {"fichier": C.SRC_FINANCE, "lignes": len(fi), "doublons": 0,
         "couverture_temporelle": C.SOURCES[C.SRC_FINANCE]["periode"],
         "couverture_geographique": f"5 régions · {fi.prefecture.nunique()} préfectures · {fi.commune.nunique()} communes · {fi.canton.nunique()} cantons",
         "valeurs_non_informatives": f"statut ambigu (Néant, Nsp, N/a, Autre, Location) : {(fi.statut_groupe == C.STATUT_NR).sum()} ; "
                                     f"adresse « Néant/Nsp » : {fi.shape[0] and int(pd.read_csv(C.DATA_DIR / C.SRC_FINANCE).etab_adresse.str.strip().str.lower().isin(NON_INFORMATIF).sum())}",
         "limites": f"{absents(C.SRC_FINANCE)} (nombre de guichets, GAB, clients, personnel, date de création…) ; "
                    "un enregistrement = un établissement, pas un nombre de guichets ; catégorie telle que déclarée"},
        {"fichier": C.SRC_INTERNET_BM, "lignes": len(bm), "doublons": 0,
         "couverture_temporelle": f"{int(bm.dropna().annee.min())}–{int(bm.dropna().annee.max())} renseignées ; {bm.valeur_pct.isna().sum()} années vides (dont 2023)",
         "couverture_geographique": "National", "valeurs_non_informatives": "—",
         "limites": "Aucune ventilation territoriale, par sexe ou par âge ; méthodologie UIT (estimations possibles)"},
        {"fichier": C.SRC_TELECOM_INTERNET, "lignes": int((tel.fichier == C.SRC_TELECOM_INTERNET).sum()), "doublons": 0,
         "couverture_temporelle": "2013–2019 (séries partielles : 4G Moov 2013–2017, EV-DO 2013–2017, Illiconet 2013–2014, LS point à point 2013)",
         "couverture_geographique": "National",
         "valeurs_non_informatives": "—",
         "limites": "Producteur non indiqué ; unité « Nombre » pour des taux en % ; opérateur non précisé pour les offres fixes ; pas de série après 2019"},
        {"fichier": C.SRC_TELECOM_MARCHE, "lignes": int((tel.fichier == C.SRC_TELECOM_MARCHE).sum()), "doublons": 0,
         "couverture_temporelle": "2013–2019", "couverture_geographique": "National",
         "valeurs_non_informatives": "—",
         "limites": "ARPU incohérent avec l'unité (exclu) ; périmètre du CA et de l'investissement non précisé ; CA et investissement non ventilés par opérateur"},
        {"fichier": C.SRC_POPULATION, "lignes": len(hier), "doublons": 0,
         "couverture_temporelle": "2022 (RGPH-5)",
         "couverture_geographique": "Pays · 6 régions RGPH (dont DAGL) · 39 préfectures · 116 unités communales · 597 cantons/quartiers",
         "valeurs_non_informatives": "—",
         "limites": "Niveau non indiqué dans le fichier (reconstruit par les sommes) ; Danyi 1 et 2 fusionnées ; "
                    "3 libellés de communes erronés ; cantons non appariables de façon fiable aux cantons PRISE (orthographes, quartiers du Grand Lomé)"},
    ])


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]).replace("|", "/").replace("\n", " ") for c in cols) + " |")
    return "\n".join(out)


def ecrire_markdown(dico: pd.DataFrame, sch: pd.DataFrame, journal: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> str:
    parties = ["# Dictionnaire de données", "",
               "Généré automatiquement par `src/audit.py` (lancé par `python -m src.pipeline`). "
               "Les fichiers de `data/` sont lus sans modification.", "",
               "## 1. Fichiers sources", ""]
    parties.append(_md_table(pd.DataFrame([{"fichier": f, "contenu": C.SOURCES[f]["titre"], "producteur": C.SOURCES[f]["producteur"],
                                             "période": C.SOURCES[f]["periode"], "granularité": C.SOURCES[f]["granularite"]}
                                            for f in C.SOURCES])))
    parties += ["", "## 2. Colonnes des fichiers de données", ""]
    for f in DONNEES:
        d = dico[dico.fichier == f][["colonne", "type", "non_nuls", "taux_manquant_pct", "taux_non_informatif_pct",
                                     "valeurs_distinctes", "min", "max", "exemples"]]
        parties += [f"### `{f}`", "", f"*{C.SOURCES[f]['titre']}* — période : {d.shape and dico[dico.fichier == f].periode.iloc[0]} — "
                    f"granularité : {C.SOURCES[f]['granularite']}", "", _md_table(d), ""]
    parties += ["## 3. Champs décrits dans les schémas mais absents des fichiers fournis", "",
                "Les fichiers `agents-mobile-money.csv` et `finance-etablissements.csv` décrivent la structure complète des couches. "
                "Les extractions fournies n'en contiennent qu'une partie : toute analyse reposant sur les champs absents est impossible.", ""]
    for f, g in sch.groupby("fichier_donnees"):
        pres = g[g.present_dans_les_donnees].champ.tolist()
        abs_ = g[~g.present_dans_les_donnees]
        parties += [f"### `{f}` — {len(pres)} champs présents / {len(g)} décrits", "",
                    "Présents : " + ", ".join(f"`{c}`" for c in pres), "",
                    "Absents : " + ", ".join(f"`{c}`" for c in abs_.champ), ""]
    parties += ["## 4. Journal de qualité des données observées", "", _md_table(journal), "",
                "## 5. Tables produites (`data_processed/`)", ""]
    rows = []
    for nom, df in tables.items():
        rows.append({"table": f"`{nom}.csv`", "lignes": len(df), "colonnes": ", ".join(df.columns[:14]) + (" …" if df.shape[1] > 14 else "")})
    parties += [_md_table(pd.DataFrame(rows)), "",
                "Géométries : `geo_prefectures.geojson`, `geo_regions.geojson`, `geo_pays.geojson` (contours COD-AB OCHA "
                "réconciliés au Défi 1, simplifiés à ~250 m pour l'affichage). Contrôles : `controles_qualite.csv`.", ""]
    return "\n".join(parties)


def generer_audit(tables: dict[str, pd.DataFrame]) -> None:
    dico = dictionnaire_sources()
    sch = champs_schema()
    journal = journal_qualite(tables)
    dico.to_csv(C.PROCESSED_DIR / "dictionnaire_donnees.csv", index=False, encoding="utf-8")
    sch.to_csv(C.PROCESSED_DIR / "schema_champs.csv", index=False, encoding="utf-8")
    journal.to_csv(C.PROCESSED_DIR / "journal_qualite.csv", index=False, encoding="utf-8")
    (C.ROOT / "data_dictionary.md").write_text(ecrire_markdown(dico, sch, journal, tables), encoding="utf-8")
