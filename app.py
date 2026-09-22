"""Tableau de bord — Adoption du numérique et inclusion financière par le mobile money au Togo.

Lancement : streamlit run app.py
"""
from __future__ import annotations

import os

import streamlit as st

from src import config as C
from src import ui
from src.data import DonneesManquantes

st.set_page_config(page_title="Inclusion numérique · Togo", page_icon=str(C.ASSETS_DIR / "favicon-96x96.png"),
                   layout="wide", initial_sidebar_state="auto")
ui.injecter_css()
st.logo(str(C.ASSETS_DIR / "logo.svg"), size="large", icon_image=str(C.ASSETS_DIR / "armoiries.svg"))

try:
    from src.contexte import tables
    from src.etat import barre_laterale

    T = tables()
except DonneesManquantes as e:
    ui.entete("Données indisponibles", "Lancez d'abord le pipeline : python -m src.pipeline")
    ui.vide(str(e), titre="Tables préparées introuvables")
    st.stop()

# Page d'ouverture : l'accueil, sauf pour les tests automatisés (DASHBOARD_PAGE_INITIALE=pages/xxx.py)
PAGE_INITIALE = os.environ.get("DASHBOARD_PAGE_INITIALE", "pages/accueil.py")


def page(chemin: str, titre: str, icone: str) -> st.Page:
    return st.Page(chemin, title=titre, icon=icone, default=chemin == PAGE_INITIALE)


pages = {
    "Synthèse": [page("pages/accueil.py", "Vue d'ensemble", ":material/space_dashboard:")],
    "Analyses": [
        page("pages/internet.py", "Usage d'Internet", ":material/language:"),
        page("pages/telecoms.py", "Télécommunications", ":material/cell_tower:"),
        page("pages/services_financiers.py", "Services financiers", ":material/account_balance:"),
        page("pages/inclusion.py", "Inclusion territoriale", ":material/map:"),
    ],
    "Décision": [page("pages/recommandations.py", "Recommandations", ":material/flag:")],
    "Référence": [page("pages/methodologie.py", "Méthodologie", ":material/menu_book:")],
}
nav = st.navigation(pages, position="sidebar")
barre_laterale(T["pop_commune"])
nav.run()
