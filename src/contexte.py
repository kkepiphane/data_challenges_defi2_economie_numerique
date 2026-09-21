"""Données chargées une fois (st.cache_data) et vues filtrées partagées par les pages."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from . import config as C
from . import data as D
from . import indicators as I
from .etat import filtres_courants


@st.cache_data(show_spinner="Chargement des données…")
def tables() -> dict[str, pd.DataFrame]:
    return D.charger_tout()


@st.cache_data(show_spinner=False)
def geo(cle: str) -> dict | None:
    return D.lire_geo(cle)


@st.cache_data(show_spinner=False, max_entries=64)
def agents_filtres(operateurs: tuple, inclure_nr: bool, categories: tuple, statuts: tuple) -> pd.DataFrame:
    f = I.Filtres(operateurs=operateurs, inclure_op_nr=inclure_nr, categories=categories, statuts=statuts)
    return I.filtrer_agents(tables()["agents"], f)


@st.cache_data(show_spinner=False, max_entries=64)
def finance_filtree(categories: tuple, statuts: tuple) -> pd.DataFrame:
    f = I.Filtres(categories=categories, statuts=statuts)
    return I.filtrer_finance(tables()["finance"], f)


@st.cache_data(show_spinner=False, max_entries=128)
def table_territoriale(niveau: str, f: I.Filtres) -> pd.DataFrame:
    ag = agents_filtres(f.operateurs, f.inclure_op_nr, f.categories, f.statuts)
    fi = finance_filtree(f.categories, f.statuts)
    return I.table_territoriale(niveau, ag, fi, D.populations(tables()), f)


@dataclass
class Contexte:
    f: I.Filtres
    T: dict[str, pd.DataFrame]
    agents: pd.DataFrame          # filtres service appliqués, tout le territoire
    finance: pd.DataFrame
    agents_geo: pd.DataFrame      # + filtre géographique
    finance_geo: pd.DataFrame
    pop_total: int                # population du périmètre géographique sélectionné

    @property
    def pop(self) -> dict[str, pd.DataFrame]:
        return D.populations(self.T)

    def territoire(self, niveau: str) -> pd.DataFrame:
        return table_territoriale(niveau, self.f)


def contexte() -> Contexte:
    f = filtres_courants()
    T = tables()
    ag = agents_filtres(f.operateurs, f.inclure_op_nr, f.categories, f.statuts)
    fi = finance_filtree(f.categories, f.statuts)
    per = I.perimetre(f, D.populations(T))["commune"]
    pc = T["pop_commune"]
    pop_total = int(pc.population.sum() if per is None else pc[pc.unite_commune.isin(per)].population.sum())
    return Contexte(f=f, T=T, agents=ag, finance=fi, agents_geo=I.filtrer_geo(ag, f), finance_geo=I.filtrer_geo(fi, f),
                    pop_total=pop_total)


def puces_filtres(f: I.Filtres, periode: bool | str = False, geo: bool = False, operateur: bool = False,
                  etablissements: bool = False, note_na: str = "") -> list[tuple[str, str, bool]]:
    """Puces indiquant, pour la page courante, les filtres appliqués et ceux sans objet.
    periode : True = appliquée ; texte = motif pour lequel elle est sans objet."""
    p = []
    if periode is True:
        p.append(("Période", f"{f.periode[0]}–{f.periode[1]}", True))
    else:
        p.append(("Période", periode or "sans objet", False))
    p.append(("Territoire", f.libelle_geo(), True) if geo else ("Territoire", note_na or "série nationale", False))
    ops = " + ".join(f.operateurs) or "aucun"
    if operateur:
        p.append(("Opérateurs", ops + (" + non renseigné" if f.inclure_op_nr else ""), True))
    if etablissements:
        cats = ", ".join(f.categories) if f.categories else "aucune"
        p.append(("Établissements", cats, True))
        if tuple(f.statuts) != tuple(C.STATUT_DEFAULT):
            p.append(("Statuts", ", ".join(f.statuts) or "aucun", True))
    return p
