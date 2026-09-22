"""Test de fumée : chaque page s'exécute sans exception pour des combinaisons de filtres extrêmes.

Usage : python -m pytest tests -q   (ou python tests/test_app.py)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["pages/accueil.py", "pages/internet.py", "pages/telecoms.py", "pages/services_financiers.py",
         "pages/inclusion.py", "pages/recommandations.py", "pages/methodologie.py"]

SCENARIOS = {
    "defaut": {},
    "region_savanes": {"f_regions": ["Savanes"]},
    "prefecture_sans_etablissement": {"f_regions": ["Savanes"], "f_prefectures": ["Kpendjal"]},
    "commune_fusionnee": {"f_communes": ["Danyi 1"]},
    "aucun_operateur": {"f_operateurs": []},
    "aucune_categorie": {"f_categories": []},
    "assurances_seules": {"f_categories": ["Assurance"]},
    "non_operationnels": {"f_statuts": ["Déclaré non opérationnel"]},
    "periode_ancienne": {"f_periode": (1990, 1995)},
    "periode_un_an": {"f_periode": (2019, 2019)},
    "periode_hors_telecom": {"f_periode": (2020, 2023)},
    "moov_seul_commune": {"f_operateurs": ["Moov"], "f_prefectures": ["Golfe"], "f_communes": ["Golfe 1"]},
    "niveau_region": {"niv_inclusion": "Région", "niv_reco": "Préfecture", "niv_repartition": "Région"},
    "niveau_commune": {"niv_inclusion": "Commune", "critere_inclusion": "hab_par_etab", "niv_repartition": "Canton"},
    "region_critere_distance": {"f_regions": ["Kara"], "niv_inclusion": "Région", "critere_inclusion": "dist_mediane_km"},
    "vues_carte": {"vue_carte": "Opérateurs", "couches_carte": ["Agents MM", "Établissements", "Population"]},
    "vue_densite": {"vue_carte": "Densité", "couches_carte": ["Agents MM", "Établissements"]},
    "comparaison_internet": {"cmp_abonnements": "Taux de pénétration par abonnements (2013–2019)", "f_periode": (2010, 2023)},
    "comparaison_hors_periode": {"cmp_abonnements": "Taux de pénétration par abonnements (2013–2019)", "f_periode": (2000, 2010)},
}


def executer(scenario: dict, page: str) -> list[str]:
    """Lance l'application complète (barre latérale comprise) en ouvrant directement la page testée."""
    os.environ["DASHBOARD_PAGE_INITIALE"] = page
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
    for k, v in scenario.items():
        at.session_state[k] = v
    at.run()
    erreurs = [str(e.value) for e in at.exception]
    if not erreurs and not any(b.key == "btn_reset" for b in at.sidebar.button):
        erreurs.append("barre latérale absente")
    return erreurs


def test_pages():
    erreurs = {}
    for nom, sc in SCENARIOS.items():
        for p in PAGES:
            ex = executer(sc, p)
            if ex:
                erreurs[f"{nom} · {p}"] = ex
    assert not erreurs, erreurs


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    n_err = 0
    for nom, sc in SCENARIOS.items():
        for p in PAGES:
            ex = executer(sc, p)
            statut = "OK " if not ex else "ERR"
            n_err += bool(ex)
            print(f"[{statut}] {nom:32} {p}" + ("" if not ex else f"\n      {ex[0][:400]}"))
    print(f"\n{len(SCENARIOS) * len(PAGES)} exécutions · {n_err} en erreur")
    sys.exit(1 if n_err else 0)
