"""Vue d'ensemble : indicateurs clés, carte de synthèse, constats et tableau régional."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.contexte import contexte, geo, puces_filtres
from src.formatage import compact, entier, nombre, pct, pp

ctx = contexte()
f = ctx.f
bm = I.phases_internet(ctx.T["internet_bm"])
tel = ctx.T["telecom"]

nat = I.synthese_nationale(ctx.agents_geo, ctx.finance_geo, ctx.pop_total)
communes = ctx.territoire("commune")
prefs = ctx.territoire("prefecture")
regions = ctx.territoire("region")
mm_seul = communes[communes.statut_couverture == I.STATUT_MM_SEUL]

ui.entete(
    "Vue d'ensemble",
    f"Le mobile money est présent dans toutes les communes ; {len(mm_seul)} d'entre elles n'ont aucun établissement financier recensé."
    if len(mm_seul) else "Chaque commune du périmètre compte au moins un établissement financier recensé.",
    puces_filtres(f, geo=True, operateur=True, etablissements=True),
)

# --------------------------------------------------------------------------------------
ui.titre_section("Numérique", "Séries nationales")
der = bm.dropna(subset=["valeur_pct"]).iloc[-1]
v2013 = bm.loc[bm.annee == 2013, "valeur_pct"].iloc[0]
ab = I.serie(tel, "T abonnés Internet Fixe et Mobile (Toutes technologies)")
pen = I.serie(tel, "Taux de pénétration Internet (Toutes technologies) (%)")
tele = I.serie(tel, "Télédensité mobile GSM")
gsm = I.serie(tel, "Le nombre total d'abonnées mobiles GSM")
hhi = I.hhi_parts(tel).set_index("annee")
ui.rangee_kpi([
    ui.kpi("Usage d'Internet", nombre(der.valeur_pct), f"{pp(der.valeur_pct - v2013)} depuis 2013",
           "Banque mondiale", str(int(der.annee)), unite="%"),
    ui.kpi("Abonnements Internet", compact(ab.iloc[-1]), f"Pénétration : {pct(pen.iloc[-1])}",
           "Séries sectorielles", str(ab.index[-1])),
    ui.kpi("Télédensité mobile", nombre(tele.iloc[-1]), f"{compact(gsm.iloc[-1])} abonnés GSM",
           "Séries sectorielles", str(tele.index[-1]), unite="%"),
    ui.kpi("Concentration du marché", entier(hhi.hhi.iloc[-1]),
           f"Togocom {pct(hhi.Togocom.iloc[-1])} · Moov {pct(hhi.Moov.iloc[-1])}",
           "Indice HHI", str(int(hhi.index[-1]))),
])

# --------------------------------------------------------------------------------------
ui.titre_section("Services financiers", "Points de service géolocalisés")
n_unites = len(communes)
ui.rangee_kpi([
    ui.kpi("Agents mobile money", entier(nat["agents"]), f"{entier(nat['hab_par_agent'])} hab. par agent",
           "Géoportail PRISE", "2021/22"),
    ui.kpi("Établissements financiers", entier(nat["etablissements"]),
           f"{entier(nat['hab_par_etab'])} hab. par établissement" if nat["etablissements"] else "Aucun dans la sélection",
           "Dépôt et crédit, 01/2025"),
    ui.kpi("Agents par établissement", nombre(nat["agents_par_etab"]),
           f"{pct(nat['part_eloignes_pct'])} à plus de {C.SEUIL_ELOIGNEMENT_KM} km", "Calcul"),
    ui.kpi("Communes sans établissement", f"{len(mm_seul)}", f"{entier(mm_seul.population.sum())} habitants",
           "RGPH-5 2022", ton="alert" if len(mm_seul) else "", unite=f"sur {n_unites}"),
])

# --------------------------------------------------------------------------------------
st.write("")
c1, c2 = st.columns([1.35, 1], gap="medium")
with c1:
    with ui.carte("carte_synthese"):
        ui.titre_carte("Habitants par établissement financier", "Par préfecture. En rouge : aucun établissement recensé.",
                       aide="Population RGPH-5 2022 ÷ établissements recensés (géoportail, extraction 01/2025). "
                            "Contours COD-AB OCHA (Défi 1).")
        gj = geo("prefectures")
        if gj is None:
            ui.vide("Contours préfectoraux absents.")
        elif prefs.empty:
            ui.vide("Aucun territoire ne correspond aux filtres.")
        else:
            avec = prefs[prefs.etablissements > 0]
            sans = prefs[prefs.etablissements == 0]
            fig = charts.carte(hauteur=520)
            if not avec.empty:
                charts.couche_choroplethe(
                    fig, gj, avec.rename(columns={"territoire": "prefecture"}), "prefecture", "hab_par_etab",
                    "Hab. / établissement", T.RAMPE_CHAUDE[:7],
                    [f"<b>{r.territoire}</b> ({r.region})<br>{entier(r.hab_par_etab)} hab. par établissement"
                     f"<br>{entier(r.etablissements)} établissements · {entier(r.agents)} agents MM<br>Population : {entier(r.population)}"
                     for r in avec.itertuples()])
            if not sans.empty:
                fig.add_trace(go.Choroplethmap(
                    geojson=gj, locations=sans.territoire, z=[1] * len(sans), featureidkey="properties.prefecture",
                    colorscale=[[0, T.CRITIQUE], [1, T.CRITIQUE]], showscale=False,
                    marker=dict(opacity=0.85, line=dict(color="#fff", width=1)),
                    hovertext=[f"<b>{r.territoire}</b><br>Aucun établissement recensé<br>{entier(r.agents)} agents MM · "
                               f"{entier(r.population)} hab." for r in sans.itertuples()],
                    hovertemplate="%{hovertext}<extra></extra>", name="Aucun établissement"))
            if f.geo_actif and not ctx.agents_geo.empty:
                c, z = charts._zoom(ctx.agents_geo.lat, ctx.agents_geo.lon, 520)
                fig.update_layout(map=dict(center=c, zoom=z))
            ui.graphique(fig, "carte_accueil")

with c2:
    with ui.carte("constats"):
        ui.titre_carte("Constats")
        items = []
        pic = bm.loc[bm.variation_pp.idxmax()]
        items.append(ui.constat(
            f"Usage d'Internet multiplié par {nombre(der.valeur_pct / v2013)} depuis 2013",
            f"{nombre(v2013)} % en 2013, {nombre(der.valeur_pct)} % en {int(der.annee)} ; plus forte hausse en {int(pic.annee)}."))
        if nat["agents"] and nat["etablissements"]:
            items.append(ui.constat(
                f"{nombre(nat['agents_par_etab'], 0)} agents mobile money pour un établissement",
                "L'agent est le point d'accès financier le plus répandu."))
        if len(mm_seul):
            top = mm_seul.sort_values("population", ascending=False).head(3).territoire.tolist()
            items.append(ui.constat(
                f"<b>{len(mm_seul)} communes</b> sans établissement recensé",
                f"{entier(mm_seul.population.sum())} habitants, dont {', '.join(top)}.", ton="alert"))
        if len(regions) > 1 and regions.etablissements.gt(0).all():
            hi, lo = regions.loc[regions.hab_par_etab.idxmax()], regions.loc[regions.hab_par_etab.idxmin()]
            items.append(ui.constat(
                f"Écart de 1 à {nombre(hi.hab_par_etab / lo.hab_par_etab)} entre régions",
                f"{hi.territoire} : {entier(hi.hab_par_etab)} hab. par établissement ; {lo.territoire} : {entier(lo.hab_par_etab)}."))
        if not items:
            ui.vide("Les filtres actuels ne laissent aucun point de service.", titre="Aucun constat calculable")
        st.html("".join(items))

# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("regions"):
    ui.titre_carte("Par région", aide="Dénominateur : population RGPH-5 2022 de la région. Maritime inclut le Grand Lomé.")
    if regions.empty:
        ui.vide("Aucune région dans la sélection.")
    else:
        tab = regions[["territoire", "population", "agents", "etablissements", "hab_par_agent", "hab_par_etab",
                       "agents_par_etab", "part_eloignes_pct"]].rename(columns={
            "territoire": "Région", "population": "Population", "agents": "Agents MM", "etablissements": "Établissements",
            "hab_par_agent": "Hab. / agent", "hab_par_etab": "Hab. / établissement", "agents_par_etab": "Agents / établ.",
            "part_eloignes_pct": f"Agents > {C.SEUIL_ELOIGNEMENT_KM} km (%)"})
        ordre = {r: i for i, r in enumerate(C.REGIONS)}
        tab = tab.sort_values("Région", key=lambda s: s.map(ordre))

        def _max(col):
            m = pd.to_numeric(tab[col], errors="coerce").replace([np.inf, -np.inf], np.nan).max()
            return float(m) * 1.1 if pd.notna(m) and m > 0 else 1.0

        st.dataframe(tab, hide_index=True, width="stretch", column_config={
            "Population": st.column_config.NumberColumn(format="localized"),
            "Agents MM": st.column_config.NumberColumn(format="localized"),
            "Hab. / agent": st.column_config.ProgressColumn(color="#A3A39D", format="%.0f", min_value=0, max_value=_max("Hab. / agent")),
            "Hab. / établissement": st.column_config.ProgressColumn(color="#A3A39D", format="%.0f", min_value=0, max_value=_max("Hab. / établissement")),
            "Agents / établ.": st.column_config.NumberColumn(format="%.1f"),
            f"Agents > {C.SEUIL_ELOIGNEMENT_KM} km (%)": st.column_config.NumberColumn(format="%.1f"),
        })
        ui.telecharger(tab, "synthese_regionale")

ui.note_bas("<b>Limites.</b> Points de service : photographie 2021/22, sans évolution possible. Séries télécoms arrêtées en 2019. "
            "Une absence dans les données n'est pas une absence réelle. Détails : page Méthodologie.")
