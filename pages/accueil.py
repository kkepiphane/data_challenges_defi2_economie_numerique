"""Vue exécutive : KPI calculés sur les données disponibles, constats et limites."""
import numpy as np
import pandas as pd
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
    "Vue exécutive",
    "Le mobile money maille le territoire ; l'offre financière formelle reste concentrée",
    f"Périmètre : <b>{f.libelle_geo()}</b> — {entier(ctx.pop_total)} habitants (RGPH-5 2022). "
    f"Chaque indicateur affiche sa dernière année réellement disponible et sa source.",
    puces_filtres(f, periode="sans objet — dernières valeurs", geo=True, operateur=True, etablissements=True),
)

# --------------------------------------------------------------------------------------
# KPI — adoption du numérique (séries nationales)
# --------------------------------------------------------------------------------------
ui.titre_section("Adoption du numérique", "Séries nationales : non affectées par les filtres territoriaux.")
der = bm.dropna(subset=["valeur_pct"]).iloc[-1]
v2013 = bm.loc[bm.annee == 2013, "valeur_pct"].iloc[0]
ab = I.serie(tel, "T abonnés Internet Fixe et Mobile (Toutes technologies)")
pen = I.serie(tel, "Taux de pénétration Internet (Toutes technologies) (%)")
tele = I.serie(tel, "Télédensité mobile GSM")
gsm = I.serie(tel, "Le nombre total d'abonnées mobiles GSM")
hhi = I.hhi_parts(tel).set_index("annee")
a_max = int(hhi.index.max())
ui.rangee_kpi([
    ui.kpi("Individus utilisant Internet", nombre(der.valeur_pct), f"{pp(der.valeur_pct - v2013)} depuis 2013 · ×{nombre(der.valeur_pct / v2013)}",
           "Banque mondiale (WDI/UIT)", str(int(der.annee)), "globe", unite="%"),
    ui.kpi("Abonnements Internet", compact(ab.iloc[-1]), f"Pénétration par abonnements : {pct(pen.iloc[-1])}",
           "Séries sectorielles", str(ab.index[-1]), "signal", "indigo"),
    ui.kpi("Télédensité mobile GSM", nombre(tele.iloc[-1]), f"{compact(gsm.iloc[-1])} abonnés mobiles GSM",
           "Séries sectorielles", str(tele.index[-1]), "phone", "indigo", unite="%"),
    ui.kpi("Concentration du marché mobile", entier(hhi.hhi.iloc[-1]),
           f"Duopole · Togocom {pct(hhi.Togocom.iloc[-1])} / Moov {pct(hhi.Moov.iloc[-1])}",
           "Indice HHI (parts en abonnés)", str(a_max), "pie", "gold"),
])

# --------------------------------------------------------------------------------------
# KPI — accès aux services financiers (dépendants des filtres)
# --------------------------------------------------------------------------------------
ui.titre_section("Accès aux services financiers", "Points de service géolocalisés — réagissent à tous les filtres de la barre latérale.")
n_unites = len(communes)
ui.rangee_kpi([
    ui.kpi("Agents mobile money", entier(nat["agents"]), f"{entier(nat['hab_par_agent'])} habitants par agent",
           "Géoportail PRISE", "2021/22", "phone"),
    ui.kpi("Établissements financiers", entier(nat["etablissements"]),
           f"{entier(nat['hab_par_etab'])} habitants par établissement" if nat["etablissements"] else "Aucun établissement dans la sélection",
           "Géoportail (extraction 01/2025)", "n.d.", "bank", "indigo"),
    ui.kpi("Agents MM par établissement", nombre(nat["agents_par_etab"]),
           f"{pct(nat['part_eloignes_pct'])} des agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km d'un établissement",
           "Agents ÷ établissements", "PRISE 21/22 · extr. 2025", "layers", "gold"),
    ui.kpi("Communes sans établissement", f"{len(mm_seul)}", f"sur {n_unites} unités communales · "
           f"{entier(mm_seul.population.sum())} hab. ({pct(100 * mm_seul.population.sum() / max(ctx.pop_total, 1))})",
           "Agents MM présents, aucun établissement", "Pop. 2022", "alert", "alert", unite=f"/ {n_unites}"),
])
ui.source("« n.d. » : la date de collecte des établissements n'est pas présente dans le fichier fourni (extraction du 08/01/2025). "
          "Population : RGPH-5 2022. Un établissement = un point de service recensé (le nombre de guichets par établissement est absent des données).")

# --------------------------------------------------------------------------------------
# Carte + constats
# --------------------------------------------------------------------------------------
st.write("")
c1, c2 = st.columns([1.35, 1], gap="medium")
with c1:
    with ui.carte("carte_synthese"):
        ui.titre_carte("Habitants par établissement financier, par préfecture",
                       "Plus la teinte est foncée, moins l'offre formelle est dense. Rouge : aucun établissement observé.")
        gj = geo("prefectures")
        if gj is None:
            ui.vide("Contours préfectoraux absents : la carte ne peut pas être tracée.")
        elif prefs.empty:
            ui.vide("Aucun territoire ne correspond aux filtres.")
        else:
            avec = prefs[prefs.etablissements > 0]
            sans = prefs[prefs.etablissements == 0]
            fig = charts.carte(hauteur=520)
            if not avec.empty:
                charts.couche_choroplethe(
                    fig, gj, avec.rename(columns={"territoire": "prefecture"}), "prefecture", "hab_par_etab",
                    "Hab. / établissement", T.RAMPE_CHAUDE[:6],
                    [f"<b>{r.territoire}</b> ({r.region})<br>{entier(r.hab_par_etab)} hab. par établissement"
                     f"<br>{entier(r.etablissements)} établissements · {entier(r.agents)} agents MM<br>Population : {entier(r.population)}"
                     for r in avec.itertuples()])
            if not sans.empty:
                import plotly.graph_objects as go
                fig.add_trace(go.Choroplethmap(
                    geojson=gj, locations=sans.territoire, z=[1] * len(sans), featureidkey="properties.prefecture",
                    colorscale=[[0, T.CRITIQUE], [1, T.CRITIQUE]], showscale=False, marker=dict(opacity=0.85, line=dict(color="#fff", width=1)),
                    hovertext=[f"<b>{r.territoire}</b><br>Aucun établissement observé<br>{entier(r.agents)} agents MM · "
                               f"{entier(r.population)} hab." for r in sans.itertuples()],
                    hovertemplate="%{hovertext}<extra></extra>", name="Aucun établissement observé"))
            if f.geo_actif:
                pts = ctx.agents_geo
                if not pts.empty:
                    c, z = charts._zoom(pts.lat, pts.lon, 520)
                    fig.update_layout(map=dict(center=c, zoom=z))
            ui.graphique(fig, "carte_accueil")
        ui.source("<b>Sources</b> : établissements (géoportail, extraction 01/2025) · RGPH-5 2022 · contours COD-AB OCHA (Défi 1). "
                  "<b>Formule</b> : population ÷ établissements recensés (catégories et statuts filtrés).")

with c2:
    with ui.carte("constats"):
        ui.titre_carte("Principaux constats", "Calculés sur le périmètre et les filtres actifs.")
        items = []
        pic = bm.loc[bm.variation_pp.idxmax()]
        items.append(ui.constat(
            f"Usage d'Internet multiplié par {nombre(der.valeur_pct / v2013)} depuis 2013",
            f"De {nombre(v2013)} % à {nombre(der.valeur_pct)} % de la population ({int(der.annee)}) ; plus forte hausse annuelle en "
            f"{int(pic.annee)} ({pp(pic.variation_pp)}). Aucune donnée 2023.", "trend"))
        if nat["agents"] and nat["etablissements"]:
            items.append(ui.constat(
                f"{nombre(nat['agents_par_etab'], 0)} agents MM pour un établissement financier",
                f"{entier(nat['agents'])} agents contre {entier(nat['etablissements'])} établissements de la sélection : "
                f"le réseau d'agents est le point d'accès le plus répandu.", "layers", "gold"))
        if len(mm_seul):
            top = mm_seul.sort_values("population", ascending=False).head(3).territoire.tolist()
            items.append(ui.constat(
                f"{len(mm_seul)} communes desservies uniquement par des agents MM",
                f"{entier(mm_seul.population.sum())} habitants sans établissement observé ; les plus peuplées : {', '.join(top)}.",
                "alert", "alert"))
        if len(regions) > 1 and regions.etablissements.gt(0).all():
            hi, lo = regions.loc[regions.hab_par_etab.idxmax()], regions.loc[regions.hab_par_etab.idxmin()]
            items.append(ui.constat(
                f"Écart de 1 à {nombre(hi.hab_par_etab / lo.hab_par_etab)} entre régions",
                f"{hi.territoire} : {entier(hi.hab_par_etab)} hab. par établissement ; {lo.territoire} : {entier(lo.hab_par_etab)}.", "bank"))
        if pd.notna(nat["part_eloignes_pct"]):
            items.append(ui.constat(
                f"{pct(nat['part_eloignes_pct'])} des agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km d'un établissement",
                f"Distance médiane agent → établissement : {nombre(nat['dist_mediane_km'], 2)} km (vol d'oiseau).", "ruler"))
        if not items:
            ui.vide("Les filtres actuels ne laissent aucun point de service à analyser.", titre="Aucun constat calculable")
        st.html("".join(items))

# --------------------------------------------------------------------------------------
# Tableau régional
# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("regions"):
    ui.titre_carte("Tableau de bord régional", "Dénominateur : population RGPH-5 2022 de la même région (Maritime inclut le Grand Lomé).")
    if regions.empty:
        ui.vide("Aucune région dans la sélection.")
    else:
        tab = regions[["territoire", "population", "agents", "etablissements", "hab_par_agent", "hab_par_etab",
                       "agents_par_etab", "part_eloignes_pct"]].rename(columns={
            "territoire": "Région", "population": "Population 2022", "agents": "Agents MM", "etablissements": "Établissements",
            "hab_par_agent": "Hab. / agent", "hab_par_etab": "Hab. / établissement", "agents_par_etab": "Agents / établissement",
            "part_eloignes_pct": f"Agents > {C.SEUIL_ELOIGNEMENT_KM} km (%)"})
        ordre = {r: i for i, r in enumerate(C.REGIONS)}
        tab = tab.sort_values("Région", key=lambda s: s.map(ordre))
        def _max(col):
            m = pd.to_numeric(tab[col], errors="coerce").replace([np.inf, -np.inf], np.nan).max()
            return float(m) * 1.1 if pd.notna(m) and m > 0 else 1.0

        st.dataframe(tab, hide_index=True, width="stretch", column_config={
            "Population 2022": st.column_config.NumberColumn(format="localized"),
            "Agents MM": st.column_config.NumberColumn(format="localized"),
            "Hab. / agent": st.column_config.ProgressColumn(format="%.0f", min_value=0, max_value=_max("Hab. / agent")),
            "Hab. / établissement": st.column_config.ProgressColumn(format="%.0f", min_value=0, max_value=_max("Hab. / établissement")),
            "Agents / établissement": st.column_config.NumberColumn(format="%.1f"),
            f"Agents > {C.SEUIL_ELOIGNEMENT_KM} km (%)": st.column_config.NumberColumn(format="%.1f %%"),
        })
        ui.telecharger(tab, "synthese_regionale")

# --------------------------------------------------------------------------------------
# Limites
# --------------------------------------------------------------------------------------
ui.titre_section("À garder en tête")
l1, l2, l3 = st.columns(3, gap="small")
with l1:
    ui.encadre("<b>Photographie, pas tendance.</b> Agents collectés en 2021/22 (PRISE) ; date de collecte des établissements absente. "
               "Aucune évolution des points de service n'est calculable.", "warn", "calendar")
with l2:
    ui.encadre("<b>Séries télécoms arrêtées en 2019.</b> Usage d'Internet disponible jusqu'en 2022 (Banque mondiale), "
               "sans ventilation territoriale ni par sexe.", "warn", "database")
with l3:
    ui.encadre("<b>Absence dans les données ≠ absence réelle.</b> Un territoire sans établissement recensé peut être servi par un point "
               "non collecté. Distances à vol d'oiseau, pas temps de trajet.", "warn", "alert")
