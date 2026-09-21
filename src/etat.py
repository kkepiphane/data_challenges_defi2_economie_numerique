"""Filtres globaux : état persistant entre les pages, barre latérale et réinitialisation."""
from __future__ import annotations

import copy

import pandas as pd
import streamlit as st

from . import config as C
from .indicators import Filtres

DEFAUTS = {
    "f_periode": C.PERIODE_DEFAUT,
    "f_regions": [],
    "f_prefectures": [],
    "f_communes": [],
    "f_operateurs": list(C.OPERATEURS),
    "f_op_nr": True,
    "f_categories": list(C.FIN_CATEGORIES_DEFAULT),
    "f_statuts": list(C.STATUT_DEFAULT),
}


def initialiser() -> None:
    for k, v in DEFAUTS.items():
        if k not in st.session_state:
            st.session_state[k] = copy.deepcopy(v)


def reinitialiser() -> None:
    for k, v in DEFAUTS.items():
        st.session_state[k] = copy.deepcopy(v)


def _nettoyer(cle: str, options: list[str]) -> None:
    st.session_state[cle] = [v for v in st.session_state.get(cle, []) if v in options]


def _norm(v):
    return tuple(v) if isinstance(v, (list, tuple)) else v


def nb_filtres_actifs() -> int:
    return sum(_norm(st.session_state.get(k)) != _norm(v) for k, v in DEFAUTS.items())


def barre_laterale(pop_commune: pd.DataFrame) -> None:
    initialiser()
    geo = pop_commune.assign(communes=pop_commune.communes_bdd.str.split("|")).explode("communes")
    with st.sidebar:
        st.markdown("##### Filtres globaux")
        st.slider("Période des séries temporelles", C.ANNEE_MIN, C.ANNEE_MAX, key="f_periode",
                  help="S'applique aux séries Internet (1990–2022) et télécoms (2013–2019). "
                       "Les points de service n'ont pas de date de collecte individuelle.")
        st.multiselect("Région", C.REGIONS, key="f_regions", placeholder="Toutes les régions")
        prefs = sorted(geo[geo.region.isin(st.session_state.f_regions)].prefecture.unique()
                       if st.session_state.f_regions else geo.prefecture.unique())
        _nettoyer("f_prefectures", prefs)
        st.multiselect("Préfecture", prefs, key="f_prefectures", placeholder="Toutes les préfectures")
        g = geo
        if st.session_state.f_prefectures:
            g = g[g.prefecture.isin(st.session_state.f_prefectures)]
        elif st.session_state.f_regions:
            g = g[g.region.isin(st.session_state.f_regions)]
        communes = sorted(g.communes.unique(), key=lambda s: (s.rsplit(" ", 1)[0], int(s.rsplit(" ", 1)[1])))
        _nettoyer("f_communes", communes)
        st.multiselect("Commune", communes, key="f_communes", placeholder="Toutes les communes")
        st.pills("Opérateurs mobile money", C.OPERATEURS, selection_mode="multi", key="f_operateurs",
                 help="Un agent est retenu s'il sert au moins un opérateur sélectionné. S'applique aussi aux séries par opérateur.")
        st.checkbox("Inclure les agents à opérateur non renseigné", key="f_op_nr",
                    help="1 348 agents (6,8 %) portent la mention « Nsp » dans la source.")
        st.multiselect("Catégories d'établissements financiers", C.FIN_CATEGORIES, key="f_categories",
                       placeholder="Aucune catégorie",
                       help="Par défaut : établissements de dépôt et de crédit (banques, micro-finance, mutuelles). "
                            "Les assurances sont activables.")
        st.multiselect("Statut déclaré des établissements", C.STATUT_GROUPES, key="f_statuts", placeholder="Aucun statut",
                       help="« Déclaré non opérationnel » : fermé, en construction, inachevé, abandonné, en réfection, sans local.")
        n = nb_filtres_actifs()
        st.button(f"Réinitialiser les filtres{f' ({n})' if n else ''}", on_click=reinitialiser,
                  icon=":material/restart_alt:", width="stretch", disabled=n == 0, key="btn_reset")
        st.html('<div class="brand-foot">Sources : RGPH-5 2022 · Géoportail PRISE · Banque mondiale · '
                'séries télécoms 2013–2019. Aucune valeur imputée.</div>')


def filtres_courants() -> Filtres:
    initialiser()
    s = st.session_state
    return Filtres(
        periode=tuple(s.f_periode),
        regions=tuple(s.f_regions), prefectures=tuple(s.f_prefectures), communes=tuple(s.f_communes),
        operateurs=tuple(s.f_operateurs or ()), inclure_op_nr=bool(s.f_op_nr),
        categories=tuple(s.f_categories), statuts=tuple(s.f_statuts),
    )
