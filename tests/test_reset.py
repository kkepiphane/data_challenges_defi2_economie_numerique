"""Test de réinitialisation : après un filtre « Savanes » et des filtres de page, « Réinitialiser » doit
restituer exactement le contenu national (KPI, textes, tableaux, graphiques) de chaque page.

Usage : python tests/test_reset.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "pages/accueil.py": {},
    "pages/internet.py": {"cmp_abonnements": "Taux de pénétration par abonnements (2013–2019)", "seuil_stagnation": 1.0},
    "pages/telecoms.py": {"f_operateurs": ["Moov"]},
    "pages/services_financiers.py": {"vue_carte": "Densité", "niv_repartition": "Commune"},
    "pages/inclusion.py": {"niv_inclusion": "Commune", "critere_inclusion": "hab_par_etab"},
    "pages/recommandations.py": {"niv_reco": "Préfecture", "prio_sel": ["Priorité 1"]},
    "pages/methodologie.py": {"ctrl_vue": "Écarts seulement"},
}


def signature(at: AppTest) -> str:
    """Empreinte du contenu affiché : HTML, textes, tableaux et données des graphiques."""
    parts = [h.proto.body for h in at.get("html")]
    parts += [str(m.value) for m in at.markdown]
    for df in at.dataframe:
        try:
            parts.append(df.value.to_csv(index=False))
        except Exception:
            parts.append(str(df.proto)[:4000])
    for fig in at.get("plotly_chart"):
        spec = json.loads(fig.proto.spec)
        parts.append(json.dumps([t.get("y") or t.get("z") or t.get("x") or t.get("lat") for t in spec.get("data", [])],
                                default=str)[:20000])
    return hashlib.sha256("||".join(parts).encode()).hexdigest()


def lancer(page: str, etat: dict | None = None) -> AppTest:
    os.environ["DASHBOARD_PAGE_INITIALE"] = page
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
    for k, v in (etat or {}).items():
        at.session_state[k] = v
    at.run()
    return at


def verifier(page: str, filtres_page: dict) -> tuple[bool, str]:
    ref = signature(lancer(page))
    at = lancer(page, {"f_regions": ["Savanes"], **filtres_page})
    modif = signature(at)
    bouton = at.button(key="btn_reset")
    if bouton.disabled:
        return False, "bouton désactivé alors que des filtres sont actifs"
    bouton.click().run()
    apres = signature(at)
    if at.exception:
        return False, str(at.exception[0].value)
    reste = [k for k in ["f_regions", *filtres_page] if k in at.session_state and k != "f_regions" and
             at.session_state[k] == filtres_page.get(k)]
    ok = apres == ref and modif != ref and at.button(key="btn_reset").disabled and not reste
    return ok, f"filtré≠national : {modif != ref} · après reset = national : {apres == ref} · " \
               f"bouton désactivé après reset : {at.button(key='btn_reset').disabled} · filtres de page restants : {reste}"


if __name__ == "__main__":
    echecs = 0
    for page, fp in PAGES.items():
        ok, detail = verifier(page, fp)
        echecs += not ok
        print(f"[{'OK ' if ok else 'ERR'}] {page:32} {detail}")
    sys.exit(1 if echecs else 0)
