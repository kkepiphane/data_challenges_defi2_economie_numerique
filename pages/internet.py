"""Adoption d'Internet : série longue Banque mondiale, variations annuelles et phases."""
import pandas as pd
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.contexte import contexte, puces_filtres
from src.formatage import entier, nombre, pct, pp

ctx = contexte()
f = ctx.f
a0, a1 = f.periode

_s = I.phases_internet(ctx.T["internet_bm"]).set_index("annee").valeur_pct
_avant, _apres = (_s[2017] - _s[2013]) / 4, (_s[2022] - _s[2017]) / 5
ui.entete(
    "02 · Adoption d'Internet",
    f"De {nombre(_s[2013])} % en 2013 à {nombre(_s[2022])} % en 2022 : un rythme multiplié par {nombre(_apres / _avant)} après 2017",
    f"Gain moyen de {pp(_avant)} par an entre 2013 et 2017, puis de {pp(_apres)} par an entre 2017 et 2022 "
    "(Banque mondiale, d'après l'UIT). Les phases décrivent le rythme observé sans en attribuer la cause.",
    puces_filtres(f, periode=True),
)

with st.popover("Règles de qualification des phases", icon=":material/tune:"):
    seuil = st.slider("Seuil de stagnation (points de %)", 0.0, 2.0, 0.25, 0.05, key="seuil_stagnation",
                      help="|variation annuelle| ≤ seuil → stagnation ; variation < −seuil → recul.")
    tol = st.slider("Tolérance « rythme constant » (points)", 0.0, 1.0, 0.1, 0.05, key="tolerance_phase",
                    help="Écart à la variation de l'année précédente en deçà duquel le rythme est jugé constant.")
    st.caption("Accélération : variation > variation précédente + tolérance. Progression ralentie : variation positive "
               "mais inférieure à la précédente − tolérance.")

bm_all = I.phases_internet(ctx.T["internet_bm"], seuil, tol)
d = bm_all[(bm_all.annee >= a0) & (bm_all.annee <= a1)].copy()
brut = ctx.T["internet_bm"]
manquantes = brut[brut.valeur_pct.isna() & brut.annee.between(a0, a1)].annee.tolist()

if len(d) < 2:
    ui.vide(f"La période {a0}–{a1} contient moins de deux années renseignées : aucune variation calculable. "
            "Élargissez la période dans la barre latérale.", titre="Données insuffisantes pour cette période")
    st.stop()

debut, fin = d.iloc[0], d.iloc[-1]
n = int(fin.annee - debut.annee)
pic = d.loc[d.variation_pp.idxmax()] if d.variation_pp.notna().any() else None
tc = I.tcam(debut.valeur_pct, fin.valeur_pct, n)
ui.rangee_kpi([
    ui.kpi("Dernière valeur disponible", nombre(fin.valeur_pct), "de la population utilise Internet",
           "Banque mondiale (WDI/UIT)", str(int(fin.annee)), "globe", unite="%"),
    ui.kpi(f"Évolution {int(debut.annee)}–{int(fin.annee)}", pp(fin.valeur_pct - debut.valeur_pct),
           f"de {nombre(debut.valeur_pct)} % à {nombre(fin.valeur_pct)} %", "Calcul : différence de niveaux",
           f"{int(debut.annee)}–{int(fin.annee)}", "trend", "gold"),
    ui.kpi("Croissance annuelle moyenne", pct(tc) if pd.notna(tc) else "—",
           "TCAM du taux d'usage" if pd.notna(tc) else "Non calculable : valeur initiale nulle", "Calcul : TCAM",
           f"{int(debut.annee)}–{int(fin.annee)}", "layers", "indigo"),
    ui.kpi("Plus forte hausse annuelle", pp(pic.variation_pp) if pic is not None else "—",
           f"en {int(pic.annee)} ({nombre(pic.valeur_pct - pic.variation_pp)} % → {nombre(pic.valeur_pct)} %)" if pic is not None else "",
           "Calcul : variation annuelle", str(int(pic.annee)) if pic is not None else "", "signal"),
])
if 2023 <= a1:
    ui.source("2023 : valeur absente du fichier Banque mondiale fourni — non estimée.")

# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("courbe"):
    ui.titre_carte("Individus utilisant Internet (% de la population)",
                   "Survolez un point pour lire la valeur, la variation et la phase.")
    comparer = st.toggle("Comparer avec les taux de pénétration par abonnements (séries sectorielles 2013–2019)",
                         key="cmp_abonnements")
    comp = None
    if comparer:
        tel = ctx.T["telecom"]
        comp = tel[(tel.famille == "Internet — pénétration") & tel.annee.between(a0, a1)][["libelle", "annee", "valeur"]]
        if comp.empty:
            ui.encadre("Aucune année 2013–2019 dans la période sélectionnée : comparaison impossible.", "warn")
            comp = None
    ui.graphique(charts.courbe_internet(d, comp, hauteur=420), "courbe_internet")
    ui.source("<b>Source</b> : Banque mondiale, World Development Indicators — indicateur « Individuals using the Internet "
              "(% of population) », fichier <i>individus-utilisant-internet-de-la-population-.csv</i>. "
              + ("<b>Lecture</b> : un taux par abonnements compte des abonnements (une personne peut en détenir plusieurs), "
                 "pas des individus ; les deux mesures ne sont pas substituables." if comparer else ""))

c1, c2 = st.columns([1.5, 1], gap="medium")
with c1:
    with ui.carte("variations"):
        ui.titre_carte("Variation annuelle et phases",
                       f"Seuil de stagnation : {nombre(seuil, 2)} pt · tolérance : {nombre(tol, 2)} pt (modifiables ci-dessus).")
        ui.graphique(charts.barres_variation(d, hauteur=330), "variation_internet")
        ui.source("<b>Formule</b> : variation = taux(année) − taux(année précédente), en points de pourcentage.")
with c2:
    with ui.carte("episodes"):
        ui.titre_carte("Épisodes successifs", "Années consécutives de même phase.")
        ep = I.episodes(d)
        if ep.empty:
            ui.vide("Aucune variation qualifiable sur la période.")
        else:
            ep_aff = ep.assign(periode=lambda x: x.debut.astype(str).where(x.debut == x.fin, x.debut.astype(str) + "–" + x.fin.astype(str)))
            st.dataframe(ep_aff[["periode", "phase", "annees", "gain_pp"]].iloc[::-1], hide_index=True, width="stretch",
                         height=330, column_config={
                             "periode": st.column_config.TextColumn("Période", width="small"),
                             "phase": st.column_config.TextColumn("Phase", width="medium"),
                             "annees": st.column_config.NumberColumn("Ans", width="small"),
                             "gain_pp": st.column_config.NumberColumn("Gain (pts)", format="%.2f", width="small")})

# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("tableau_internet"):
    ui.titre_carte("Données annuelles", "Valeurs sources et calculs dérivés — téléchargeables.")
    tab = d[["annee", "valeur_pct", "variation_pp", "croissance_pct", "phase"]].rename(columns={
        "annee": "Année", "valeur_pct": "Individus utilisant Internet (%)", "variation_pp": "Variation (pts)",
        "croissance_pct": "Croissance relative (%)", "phase": "Phase"})
    tab["Source"] = "Banque mondiale (WDI/UIT)"
    st.dataframe(tab.iloc[::-1], hide_index=True, width="stretch", height=280, column_config={
        "Année": st.column_config.NumberColumn(format="%d"),
        "Individus utilisant Internet (%)": st.column_config.NumberColumn(format="%.2f"),
        "Variation (pts)": st.column_config.NumberColumn(format="%+.2f"),
        "Croissance relative (%)": st.column_config.NumberColumn(format="%+.1f")})
    ui.telecharger(tab, f"internet_{a0}_{a1}")
    if manquantes:
        ui.source(f"Années sans valeur dans la source (non imputées) : {', '.join(map(str, manquantes))}.")

ui.encadre("<b>Pas de lecture causale.</b> Les données disponibles ne contiennent aucune variable explicative (prix, couverture "
           "réseau, revenus…) ni ventilation territoriale ou par sexe de l'usage d'Internet : les phases décrivent le rythme "
           "observé, elles n'en établissent pas les causes. Analyses territoriales de l'usage : "
           f"<b>{C.NON_DISPONIBLE.lower()}</b>.", "", "info")
