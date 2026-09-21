"""Usage d'Internet : série longue Banque mondiale, variations annuelles et phases."""
import pandas as pd
import streamlit as st

from src import charts, config as C, indicators as I, ui
from src.contexte import contexte, puces_filtres
from src.formatage import nombre, pct, pp

ctx = contexte()
f = ctx.f
a0, a1 = f.periode

_s = I.phases_internet(ctx.T["internet_bm"]).set_index("annee").valeur_pct
_avant, _apres = (_s[2017] - _s[2013]) / 4, (_s[2022] - _s[2017]) / 5
ui.entete(
    "Usage d'Internet",
    f"{nombre(_s[2022])} % de la population en 2022, contre {nombre(_s[2013])} % en 2013. "
    f"Le rythme de hausse a été multiplié par {nombre(_apres / _avant)} après 2017.",
    puces_filtres(f, periode=True),
)

with st.popover("Règles de calcul des phases", icon=":material/tune:"):
    seuil = st.slider("Seuil de stagnation (points)", 0.0, 2.0, 0.25, 0.05, key="seuil_stagnation",
                      help="|variation| ≤ seuil : stagnation ; variation < −seuil : recul.")
    tol = st.slider("Tolérance « rythme constant » (points)", 0.0, 1.0, 0.1, 0.05, key="tolerance_phase",
                    help="Accélération : variation supérieure à la précédente + tolérance.")

bm_all = I.phases_internet(ctx.T["internet_bm"], seuil, tol)
d = bm_all[(bm_all.annee >= a0) & (bm_all.annee <= a1)].copy()
brut = ctx.T["internet_bm"]
manquantes = brut[brut.valeur_pct.isna() & brut.annee.between(a0, a1)].annee.tolist()

if len(d) < 2:
    ui.vide(f"Moins de deux années renseignées entre {a0} et {a1}. Élargissez la période.", titre="Données insuffisantes")
    st.stop()

debut, fin = d.iloc[0], d.iloc[-1]
n = int(fin.annee - debut.annee)
pic = d.loc[d.variation_pp.idxmax()] if d.variation_pp.notna().any() else None
tc = I.tcam(debut.valeur_pct, fin.valeur_pct, n)
ui.rangee_kpi([
    ui.kpi("Dernière valeur", nombre(fin.valeur_pct), "de la population", "Banque mondiale", str(int(fin.annee)), unite="%"),
    ui.kpi(f"Évolution {int(debut.annee)}–{int(fin.annee)}", pp(fin.valeur_pct - debut.valeur_pct),
           f"de {nombre(debut.valeur_pct)} % à {nombre(fin.valeur_pct)} %", "Calcul"),
    ui.kpi("Croissance annuelle", pct(tc) if pd.notna(tc) else "—",
           "moyenne (TCAM)" if pd.notna(tc) else "Non calculable (valeur initiale nulle)", "Calcul"),
    ui.kpi("Plus forte hausse", pp(pic.variation_pp) if pic is not None else "—",
           f"en {int(pic.annee)}" if pic is not None else "", "Calcul"),
])

st.write("")
with ui.carte("courbe"):
    ui.titre_carte("Part de la population utilisant Internet",
                   aide="Banque mondiale, World Development Indicators (donnée UIT), "
                        "fichier individus-utilisant-internet-de-la-population-.csv.")
    comparer = st.toggle("Comparer aux taux de pénétration par abonnements (2013–2019)", key="cmp_abonnements")
    comp = None
    if comparer:
        tel = ctx.T["telecom"]
        comp = tel[(tel.famille == "Internet — pénétration") & tel.annee.between(a0, a1)][["libelle", "annee", "valeur"]]
        if comp.empty:
            ui.source("Aucune année 2013–2019 dans la période choisie.")
            comp = None
    ui.graphique(charts.courbe_internet(d, comp, hauteur=420), "courbe_internet")
    if comparer and comp is not None:
        ui.source("Un taux par abonnements compte des abonnements, pas des personnes : les deux mesures ne sont pas substituables.")

c1, c2 = st.columns([1.5, 1], gap="medium")
with c1:
    with ui.carte("variations"):
        ui.titre_carte("Variation annuelle", aide=f"Taux de l'année − taux de l'année précédente. Stagnation : ±{nombre(seuil, 2)} pt ; "
                                                  f"tolérance : {nombre(tol, 2)} pt.")
        ui.graphique(charts.barres_variation(d, hauteur=330), "variation_internet")
with c2:
    with ui.carte("episodes"):
        ui.titre_carte("Épisodes", aide="Années consécutives de même phase.")
        ep = I.episodes(d)
        if ep.empty:
            ui.vide("Aucune variation qualifiable sur la période.")
        else:
            ep_aff = ep.assign(periode=lambda x: x.debut.astype(str).where(x.debut == x.fin, x.debut.astype(str) + "–" + x.fin.astype(str)))
            st.dataframe(ep_aff[["periode", "phase", "annees", "gain_pp"]].iloc[::-1], hide_index=True, width="stretch",
                         height=330, column_config={
                             "periode": st.column_config.TextColumn("Période", width="medium"),
                             "phase": st.column_config.TextColumn("Phase", width="medium"),
                             "annees": st.column_config.NumberColumn("Ans", width="small"),
                             "gain_pp": st.column_config.NumberColumn("Gain (pts)", format="%.2f", width="small")})

st.write("")
with ui.carte("tableau_internet"):
    ui.titre_carte("Données annuelles",
                   aide=("Années sans valeur dans la source, non imputées : " + ", ".join(map(str, manquantes))) if manquantes else "")
    tab = d[["annee", "valeur_pct", "variation_pp", "croissance_pct", "phase"]].rename(columns={
        "annee": "Année", "valeur_pct": "Usage d'Internet (%)", "variation_pp": "Variation (pts)",
        "croissance_pct": "Croissance relative (%)", "phase": "Phase"})
    tab["Source"] = "Banque mondiale (WDI/UIT)"
    st.dataframe(tab.iloc[::-1], hide_index=True, width="stretch", height=280, column_config={
        "Année": st.column_config.NumberColumn(format="%d"),
        "Usage d'Internet (%)": st.column_config.NumberColumn(format="%.2f"),
        "Variation (pts)": st.column_config.NumberColumn(format="%+.2f"),
        "Croissance relative (%)": st.column_config.NumberColumn(format="%+.1f")})
    ui.telecharger(tab, f"internet_{a0}_{a1}")

ui.note_bas("<b>Lecture descriptive.</b> Aucune variable explicative ni ventilation territoriale de l'usage n'est disponible : "
            "les phases décrivent le rythme observé, sans en établir les causes."
            + (" Aucune valeur n'est publiée pour 2023." if a1 >= 2023 else ""))
