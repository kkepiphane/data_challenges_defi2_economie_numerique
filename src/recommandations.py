"""Recommandations territoriales générées par règles explicites à partir des indicateurs observés.

Aucun montant, objectif chiffré ou effet économique n'est produit : l'impact attendu est formulé
qualitativement, en désignant l'indicateur observé qui permettra de le suivre.
"""
from __future__ import annotations

import pandas as pd

from . import config as C
from .formatage import entier, km, nombre, pct

SOURCES_RECO = "RGPH-5 2022 (population) · Géoportail PRISE 2021/22 (agents MM) · Géoportail, extraction 01/2025 (établissements)"
SEUIL_DISTANCE_KM = 10
SEUIL_PART_ELOIGNES = 50
MULTIPLE_REFERENCE = 2

CRITERES = {
    "C1": "Aucun établissement de dépôt/crédit observé",
    "C2": f"Plus de {MULTIPLE_REFERENCE}× la référence nationale d'habitants par agent MM",
    "C3": f"Distance médiane agent → établissement > {SEUIL_DISTANCE_KM} km",
    "C4": f"Établissement(s) présent(s) mais ≥ {SEUIL_PART_ELOIGNES} % des agents à > {C.SEUIL_ELOIGNEMENT_KM} km",
}
REGLES = {
    "C1": "établissements (catégories et statuts sélectionnés) = 0 et agents MM > 0",
    "C2": f"habitants par agent > {MULTIPLE_REFERENCE} × (population nationale ÷ agents nationaux, mêmes filtres)",
    "C3": f"médiane des distances à vol d'oiseau des agents au plus proche établissement > {SEUIL_DISTANCE_KM} km",
    "C4": f"établissements > 0 et part des agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km ≥ {SEUIL_PART_ELOIGNES} %",
}
PRIORITES = {3: "Priorité 1", 2: "Priorité 2", 1: "Priorité 3"}
CONSTATS_COURTS = {"C1": "Aucun établissement", "C2": "Peu d'agents MM (> 2× la référence)",
                   "C3": f"1er établissement > {SEUIL_DISTANCE_KM} km (médiane)",
                   "C4": f"Agents dispersés (majorité > {C.SEUIL_ELOIGNEMENT_KM} km)"}
ACTIONS_COURTES = {"C1": "Ouvrir ou conventionner un point de dépôt/crédit (IMF, mutuelle), ou adosser des agents MM à un établissement",
                   "C2": "Densifier le réseau d'agents MM (recrutement ciblé des opérateurs)",
                   "C3": "Services financiers numériques via les agents : compte, épargne, crédit mobiles (partenariat IMF–opérateurs)",
                   "C4": "Points de service itinérants ou partenariats d'agence dans les zones dispersées"}
SUIVI = {"C1": "établissements recensés", "C2": "habitants par agent", "C3": "distance médiane",
         "C4": f"part d'agents > {C.SEUIL_ELOIGNEMENT_KM} km"}


def _criteres(r: pd.Series, ref_hab_agent: float) -> list[str]:
    c = []
    if r.agents > 0 and r.etablissements == 0:
        c.append("C1")
    if r.agents > 0 and r.hab_par_agent > MULTIPLE_REFERENCE * ref_hab_agent:
        c.append("C2")
    if pd.notna(r.dist_mediane_km) and r.dist_mediane_km > SEUIL_DISTANCE_KM:
        c.append("C3")
    if r.etablissements > 0 and pd.notna(r.part_eloignes_pct) and r.part_eloignes_pct >= SEUIL_PART_ELOIGNES:
        c.append("C4")
    return c


def generer(table: pd.DataFrame, niveau: str, ref_hab_agent: float) -> pd.DataFrame:
    lignes = []
    for _, r in table.iterrows():
        crit = _criteres(r, ref_hab_agent)
        if not crit:
            continue
        probleme, action, impact = [], [], []
        if "C1" in crit:
            probleme.append(f"{entier(r.agents)} agent(s) MM mais aucun établissement de dépôt/crédit recensé pour {entier(r.population)} habitants.")
            action.append("Implanter ou conventionner un point de service de dépôt/crédit (antenne d'IMF ou de mutuelle) ; "
                          "à défaut, adosser des agents MM existants à un établissement pour offrir dépôt, retrait et épargne.")
            impact.append(f"Premier point de service formel recensé pour {entier(r.population)} habitants (à suivre : nombre d'établissements recensés).")
        if "C2" in crit:
            probleme.append(f"{entier(r.hab_par_agent)} habitants par agent MM, contre {entier(ref_hab_agent)} au niveau national.")
            action.append("Densifier le réseau d'agents MM par un recrutement ciblé des opérateurs sur ce territoire.")
            impact.append(f"Baisse du nombre d'habitants par agent (actuellement {entier(r.hab_par_agent)}).")
        if "C3" in crit:
            probleme.append(f"Distance médiane de {km(r.dist_mediane_km)} entre les agents et l'établissement le plus proche.")
            action.append("Déployer des services financiers numériques via les agents MM (ouverture de compte, épargne et crédit mobiles "
                          "en partenariat IMF–opérateurs).")
            impact.append(f"Réduction de l'éloignement au service formel (distance médiane actuelle {km(r.dist_mediane_km)}).")
        if "C4" in crit:
            probleme.append(f"{pct(r.part_eloignes_pct, 0)} des agents sont à plus de {C.SEUIL_ELOIGNEMENT_KM} km d'un établissement, "
                            f"alors que {entier(r.etablissements)} établissement(s) existe(nt) sur le territoire.")
            action.append("Rapprocher le service formel des zones dispersées : points de service itinérants ou partenariats "
                          "d'agence avec les agents les plus éloignés.")
            impact.append(f"Baisse de la part d'agents éloignés (actuellement {pct(r.part_eloignes_pct, 0)}).")
        indicateurs = (f"Population {entier(r.population)} · Agents MM {entier(r.agents)} · Établissements {entier(r.etablissements)} · "
                       f"Hab./agent {entier(r.hab_par_agent)} · Hab./établissement "
                       f"{entier(r.hab_par_etab) if r.etablissements else 'aucun établissement'} · "
                       f"Distance médiane {km(r.dist_mediane_km)} · Agents > {C.SEUIL_ELOIGNEMENT_KM} km {pct(r.part_eloignes_pct, 0)}")
        lignes.append({
            "priorite": PRIORITES[min(len(crit), 3)], "n_criteres": len(crit), "niveau": niveau,
            "territoire": r.territoire, "prefecture": r.get("prefecture", ""), "region": r.region,
            "population": int(r.population), "agents": int(r.agents), "etablissements": int(r.etablissements),
            "hab_par_agent": r.hab_par_agent, "dist_mediane_km": r.dist_mediane_km, "part_eloignes_pct": r.part_eloignes_pct,
            "criteres": " · ".join(crit), "criteres_libelles": " · ".join(CRITERES[c] for c in crit),
            "constats_courts": " | ".join(CONSTATS_COURTS[c] for c in crit),
            "actions_courtes": " | ".join(dict.fromkeys(ACTIONS_COURTES[c] for c in crit)),
            "suivi": ", ".join(SUIVI[c] for c in crit),
            "probleme": " ".join(probleme), "indicateurs": indicateurs,
            "action": " ".join(dict.fromkeys(action)), "impact": " ".join(impact), "sources": SOURCES_RECO,
        })
    out = pd.DataFrame(lignes)
    if out.empty:
        return out
    return out.sort_values(["n_criteres", "population"], ascending=[False, False]).reset_index(drop=True)
