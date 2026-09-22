"""Filtres : état centralisé dans st.session_state, barre latérale et réinitialisation.

Deux familles de filtres :
- globaux (barre latérale), communs à toutes les pages ;
- propres à une page (niveau territorial, critère de classement, vue cartographique…).
« Réinitialiser » remet les deux familles à leur valeur par défaut (valeurs réécrites explicitement, ce qui
met aussi à jour les widgets dans le navigateur) : tous les composants sont recalculés sur le périmètre national.
"""
from __future__ import annotations

import copy

import pandas as pd
import streamlit as st

from . import config as C
from .indicators import Filtres

OPERATEURS_FILTRE = list(C.OPERATEURS) + [C.OP_NR]

DEFAUTS = {
    "f_periode": C.PERIODE_DEFAUT,
    "f_regions": [],
    "f_prefectures": [],
    "f_communes": [],
    "f_operateurs": list(OPERATEURS_FILTRE),
    "f_categories": list(C.FIN_CATEGORIES_DEFAULT),
    "f_statuts": list(C.STATUT_DEFAULT),
}

# Filtres propres aux pages : chaque page déclare la valeur par défaut de ses contrôles via valeur_page().
# Le registre est conservé dans la session ; la réinitialisation réécrit explicitement ces valeurs, ce qui
# met aussi à jour l'affichage des widgets dans le navigateur (une simple suppression de clé ne le fait pas).
REGISTRE = "_defauts_pages"
NON_COMPTES = {"dico_fichier"}


def valeur_page(cle: str, defaut) -> None:
    """Déclare la valeur par défaut d'un filtre de page et l'initialise si besoin (appeler avant le widget,
    et créer le widget sans paramètre de valeur par défaut)."""
    reg = st.session_state.setdefault(REGISTRE, {})
    reg[cle] = copy.deepcopy(defaut)
    if cle not in st.session_state:
        st.session_state[cle] = copy.deepcopy(defaut)


def initialiser() -> None:
    for k, v in DEFAUTS.items():
        if k not in st.session_state:
            st.session_state[k] = copy.deepcopy(v)


def reinitialiser() -> None:
    for k, v in DEFAUTS.items():
        st.session_state[k] = copy.deepcopy(v)
    for k, v in st.session_state.get(REGISTRE, {}).items():
        st.session_state[k] = copy.deepcopy(v)


def _nettoyer(cle: str, options: list[str]) -> None:
    valeurs = st.session_state.get(cle, [])
    propres = [v for v in valeurs if v in options]
    if propres != list(valeurs):
        st.session_state[cle] = propres


def _norm(v):
    return tuple(v) if isinstance(v, (list, tuple)) else v


def filtres_modifies() -> list[str]:
    """Clés dont la valeur diffère réellement de l'état par défaut."""
    s = st.session_state
    out = [k for k, v in DEFAUTS.items() if _norm(s.get(k)) != _norm(v)]
    for k, v in s.get(REGISTRE, {}).items():
        if k in NON_COMPTES or k not in s:
            continue
        if _norm(s[k]) != _norm(v):
            out.append(k)
    return out


def barre_laterale(pop_commune: pd.DataFrame) -> None:
    initialiser()
    geo = pop_commune.assign(communes=pop_commune.communes_bdd.str.split("|")).explode("communes")
    with st.sidebar:
        st.markdown("##### Filtres")
        st.slider("Période", C.ANNEE_MIN, C.ANNEE_MAX, key="f_periode",
                  help="Séries Internet (1990–2022) et télécoms (2013–2019). Sans effet sur les points de service, non datés.")
        st.multiselect("Région", C.REGIONS, key="f_regions", placeholder="Toutes")
        prefs = sorted(geo[geo.region.isin(st.session_state.f_regions)].prefecture.unique()
                       if st.session_state.f_regions else geo.prefecture.unique())
        _nettoyer("f_prefectures", prefs)
        st.multiselect("Préfecture", prefs, key="f_prefectures", placeholder="Toutes")
        g = geo
        if st.session_state.f_prefectures:
            g = g[g.prefecture.isin(st.session_state.f_prefectures)]
        elif st.session_state.f_regions:
            g = g[g.region.isin(st.session_state.f_regions)]
        communes = sorted(g.communes.unique(), key=lambda s: (s.rsplit(" ", 1)[0], int(s.rsplit(" ", 1)[1])))
        _nettoyer("f_communes", communes)
        st.multiselect("Commune", communes, key="f_communes", placeholder="Toutes")
        st.pills("Opérateurs mobile money", OPERATEURS_FILTRE, selection_mode="multi", key="f_operateurs",
                 help="Un agent est retenu s'il sert au moins un opérateur sélectionné. « Non renseigné » : "
                      "1 348 agents (6,8 %) portant la mention « Nsp » dans la source.")
        st.multiselect("Établissements", C.FIN_CATEGORIES, key="f_categories", placeholder="Aucune catégorie",
                       help="Par défaut : dépôt et crédit (banques, micro-finance, mutuelles).")
        st.multiselect("Statut des établissements", C.STATUT_GROUPES, key="f_statuts", placeholder="Aucun statut",
                       help="« Déclaré non opérationnel » : fermé, en construction, inachevé, abandonné, en réfection, sans local.")
        n = len(filtres_modifies())
        st.button(f"Réinitialiser{f' ({n})' if n else ''}", on_click=reinitialiser,
                  icon=":material/restart_alt:", width="stretch", disabled=n == 0, key="btn_reset",
                  help="Remet tous les filtres, y compris ceux de la page, à leur état initial (périmètre national).")
        st.html('<div class="sidebar-note">RGPH-5 2022, géoportail PRISE, Banque mondiale, séries télécoms 2013–2019.</div>')


def filtres_courants() -> Filtres:
    initialiser()
    s = st.session_state
    ops = list(s.f_operateurs or [])
    return Filtres(
        periode=tuple(s.f_periode),
        regions=tuple(s.f_regions), prefectures=tuple(s.f_prefectures), communes=tuple(s.f_communes),
        operateurs=tuple(o for o in C.OPERATEURS if o in ops), inclure_op_nr=C.OP_NR in ops,
        categories=tuple(s.f_categories), statuts=tuple(s.f_statuts),
    )
