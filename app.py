"""Tableau de bord — Adoption du numérique et inclusion financière par le mobile money au Togo.

Lancement : streamlit run app.py
"""
from __future__ import annotations

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

pages = {
    "Synthèse": [
        st.Page("pages/accueil.py", title="Vue d'ensemble", icon=":material/space_dashboard:", default=True),
    ],
    "Analyses": [
        st.Page("pages/internet.py", title="Usage d'Internet", icon=":material/language:"),
        st.Page("pages/telecoms.py", title="Télécommunications", icon=":material/cell_tower:"),
        st.Page("pages/services_financiers.py", title="Services financiers", icon=":material/account_balance:"),
        st.Page("pages/inclusion.py", title="Inclusion territoriale", icon=":material/map:"),
    ],
    "Décision": [
        st.Page("pages/recommandations.py", title="Recommandations", icon=":material/flag:"),
    ],
    "Référence": [
        st.Page("pages/methodologie.py", title="Méthodologie", icon=":material/menu_book:"),
    ],
}
nav = st.navigation(pages, position="sidebar")
barre_laterale(T["pop_commune"])
nav.run()
