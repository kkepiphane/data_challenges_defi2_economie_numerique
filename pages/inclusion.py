"""Inclusion territoriale : ratios à dénominateur de population de même granularité, classement et inégalités."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.contexte import contexte, geo, puces_filtres
from src.formatage import entier, km, nombre, pct

ctx = contexte()
f = ctx.f

com_all = ctx.territoire("commune")
mm_seul = com_all[com_all.statut_couverture == I.STATUT_MM_SEUL]
ui.entete(
    "05 · Inclusion territoriale",
    (f"{len(mm_seul)} communes ({entier(mm_seul.population.sum())} habitants) sans établissement financier recensé, seulement des agents mobile money"
     if len(mm_seul) else "Tous les territoires du périmètre disposent d'au moins un établissement observé"),
    "Ratios calculés uniquement avec la population RGPH-5 2022 du <b>même</b> territoire (région, préfecture ou commune). "
    "Le canton n'est pas utilisé comme dénominateur : ses libellés ne s'apparient pas de façon fiable entre recensement et base PRISE.",
    puces_filtres(f, periode="sans objet — photographie 2021/22", geo=True, operateur=True, etablissements=True),
)

INDICATEURS = {
    "score": "Rang moyen de sous-desserte",
    "hab_par_etab": "Habitants par établissement financier",
    "hab_par_agent": "Habitants par agent MM",
    "dist_mediane_km": "Distance médiane agent → établissement",
    "part_eloignes_pct": f"Part des agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km d'un établissement",
    "agents_par_etab": "Agents MM par établissement (poids relatif du MM)",
}
FORMAT = {"score": lambda v: nombre(v, 2), "hab_par_etab": entier, "hab_par_agent": entier, "dist_mediane_km": km,
          "part_eloignes_pct": lambda v: pct(v, 0), "agents_par_etab": lambda v: nombre(v, 1)}

c1, c2, c3 = st.columns([1.3, 1.5, 1], gap="medium", vertical_alignment="bottom")
with c1:
    niveau_lib = st.segmented_control("Niveau territorial", ["Région", "Préfecture", "Commune"], default="Préfecture", key="niv_inclusion")
niveau_lib = niveau_lib or "Préfecture"
niveau = {"Région": "region", "Préfecture": "prefecture", "Commune": "commune"}[niveau_lib]
with c2:
    critere = st.selectbox("Classer les territoires selon", list(INDICATEURS), format_func=INDICATEURS.get, key="critere_inclusion")
t = ctx.territoire(niveau)
with c3:
    top_n = st.slider("Nombre de territoires affichés", 3, max(3, min(40, len(t))), min(15, max(3, len(t))), key=f"topn_{niveau}") if len(t) > 3 else len(t)

if t.empty:
    ui.vide("Aucun territoire ne correspond aux filtres géographiques.", titre="Aucun territoire")
    st.stop()

nat = I.synthese_nationale(ctx.agents_geo, ctx.finance_geo, ctx.pop_total)
sans = t[(t.etablissements == 0) & (t.agents > 0)]
ui.rangee_kpi([
    ui.kpi("Habitants par agent MM", entier(nat["hab_par_agent"]), f"{entier(nat['agents'])} agents · {entier(ctx.pop_total)} hab.",
           "RGPH-5 2022 ÷ PRISE 2021/22", "2022", "users"),
    ui.kpi("Habitants par établissement", entier(nat["hab_par_etab"]), f"{entier(nat['etablissements'])} établissements sélectionnés",
           "RGPH-5 2022 ÷ géoportail", "2022", "bank", "indigo"),
    ui.kpi(f"Agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km", pct(nat["part_eloignes_pct"]),
           f"distance médiane {nombre(nat['dist_mediane_km'], 2)} km (vol d'oiseau)", "Calcul BallTree haversine", "—", "ruler", "gold"),
    ui.kpi(f"{niveau_lib}s MM sans établissement", f"{len(sans)}", f"{entier(sans.population.sum())} habitants concernés",
           "Agents > 0 et établissements = 0", "—", "alert", "alert", unite=f"/ {len(t)}"),
])
st.write("")

# --------------------------------------------------------------------------------------
# Carte + classement
# --------------------------------------------------------------------------------------
asc = False
val = t[critere]
t_rank = t.assign(_v=val.where(~((critere in ("hab_par_etab", "agents_par_etab")) & (t.etablissements == 0)), np.inf))
t_rank = t_rank.sort_values("_v", ascending=asc, na_position="last")
g1, g2 = st.columns([1.15, 1], gap="medium")
with g1:
    with ui.carte("carte_inclusion"):
        ui.titre_carte(f"{INDICATEURS[critere]} — {niveau_lib.lower()}s",
                       "Teinte chaude = moins bien desservi. Rouge vif : aucun établissement observé." if niveau != "commune" else
                       "Contours communaux absents des sources : points réels des agents, colorés selon la situation de leur commune.")
        gj = geo("prefectures" if niveau == "prefecture" else "regions")
        if niveau == "commune":
            ag = ctx.agents_geo.merge(t[["territoire", "statut_couverture"]], left_on="unite_commune", right_on="territoire", how="inner")
            fig = charts.carte(hauteur=560, lat=ag.lat if f.geo_actif else None, lon=ag.lon if f.geo_actif else None)
            for stt, coul, lib in [(I.STATUT_MM_ET_ETAB, T.GREEN_700, "Agents MM — commune avec établissement"),
                                   (I.STATUT_MM_SEUL, T.CRITIQUE, "Agents MM — commune sans établissement observé")]:
                sub = ag[ag.statut_couverture == stt]
                if not sub.empty:
                    charts.couche_points(fig, sub, f"{lib} ({entier(len(sub))})", coul, 5 if stt == I.STATUT_MM_SEUL else 4,
                                         0.9 if stt == I.STATUT_MM_SEUL else 0.35,
                                         ("<b>" + sub.unite_commune + "</b><br>" + stt + "<br>Établissement le plus proche : "
                                          + sub.dist_min_km.map(km)).tolist())
            fe = ctx.finance_geo
            if not fe.empty:
                charts.couche_points(fig, fe, f"Établissements financiers ({entier(len(fe))})", T.INK, 7, 0.9,
                                     ("<b>" + fe.nom + "</b><br>" + fe.categorie + " · " + fe.commune).tolist())
            ui.graphique(fig, "carte_communes")
        elif gj is None:
            ui.vide("Contours absents : carte indisponible (le classement reste valable).")
        else:
            cle = "prefecture" if niveau == "prefecture" else "region"
            avec = t[~((critere in ("hab_par_etab", "agents_par_etab")) & (t.etablissements == 0)) & t[critere].notna()]
            fig = charts.carte(hauteur=560)
            echelle = T.RAMPE_VERTE[1:7] if critere == "agents_par_etab" else T.RAMPE_CHAUDE[:6]
            if not avec.empty:
                charts.couche_choroplethe(
                    fig, gj, avec.rename(columns={"territoire": cle}), cle, critere, INDICATEURS[critere].split(" (")[0][:28], echelle,
                    [f"<b>{r.territoire}</b><br>{INDICATEURS[critere]} : <b>{FORMAT[critere](getattr(r, critere))}</b>"
                     f"<br>Population : {entier(r.population)} · agents : {entier(r.agents)} · établissements : {entier(r.etablissements)}"
                     for r in avec.itertuples()], fmt_barre=",.2f" if critere == "score" else ",.0f")
            vides = t[t.etablissements == 0]
            if not vides.empty:
                fig.add_trace(go.Choroplethmap(
                    geojson=gj, locations=vides.territoire, z=[1] * len(vides), featureidkey=f"properties.{cle}",
                    colorscale=[[0, T.CRITIQUE], [1, T.CRITIQUE]], showscale=False, marker=dict(opacity=0.85, line=dict(color="#fff", width=1)),
                    hovertext=[f"<b>{r.territoire}</b><br>Aucun établissement observé<br>{entier(r.agents)} agents MM · {entier(r.population)} hab."
                               for r in vides.itertuples()], hovertemplate="%{hovertext}<extra></extra>"))
            if f.geo_actif and not ctx.agents_geo.empty:
                c, z = charts._zoom(ctx.agents_geo.lat, ctx.agents_geo.lon, 560)
                fig.update_layout(map=dict(center=c, zoom=z))
            ui.graphique(fig, "carte_inclusion_choro")
        ui.source("<b>Sources</b> : RGPH-5 2022 · agents PRISE 2021/22 · établissements géoportail (extraction 01/2025) · contours COD-AB OCHA (Défi 1). "
                  f"<b>Formule</b> : {I.FORMULES.get(critere, '')}.")

with g2:
    with ui.carte("classement"):
        ui.titre_carte(f"Les {min(top_n, len(t_rank))} {niveau_lib.lower()}s les moins bien desservis",
                       f"Classement selon : {INDICATEURS[critere].lower()}.")
        sans_crit = t_rank[np.isinf(t_rank._v)]
        if critere in ("hab_par_etab", "agents_par_etab") and not sans_crit.empty:
            ui.encadre(f"<b>Sans établissement observé ({len(sans_crit)})</b> — ratio non calculable, placés en tête : "
                       + ", ".join(f"{r.territoire} ({entier(r.population)} hab.)" for r in sans_crit.head(12).itertuples())
                       + (" …" if len(sans_crit) > 12 else ""), "alert", "alert")
        tr = t_rank[np.isfinite(t_rank._v) & t_rank._v.notna()].head(max(0, top_n - (len(sans_crit) if critere in ("hab_par_etab", "agents_par_etab") else 0)))
        if tr.empty:
            ui.vide("Indicateur non calculable pour les territoires restants.")
        else:
            coul = T.GREEN_700 if critere == "agents_par_etab" else T.TERRACOTTA
            labels = [f"{r.territoire}" + (f" · {r.prefecture}" if niveau == "commune" else "") for r in tr.itertuples()]
            ui.graphique(charts.barres_h(labels, tr[critere], couleur=coul, texte=[FORMAT[critere](v) for v in tr[critere]],
                                         hover=[f"<b>{r.territoire}</b> ({r.region})<br>{INDICATEURS[critere]} : {FORMAT[critere](getattr(r, critere))}"
                                                f"<br>Hab./agent : {entier(r.hab_par_agent)} · Hab./établissement : "
                                                f"{entier(r.hab_par_etab) if r.etablissements else 'aucun'}"
                                                f"<br>Distance médiane : {km(r.dist_mediane_km)} · Agents > {C.SEUIL_ELOIGNEMENT_KM} km : {pct(r.part_eloignes_pct, 0)}"
                                                for r in tr.itertuples()], max_px=18), "classement")
        if critere == "score":
            ui.source(f"<b>Rang moyen</b> : {I.FORMULES['score']}. Synthèse descriptive, pas un indice pondéré.")

# --------------------------------------------------------------------------------------
# Matrice de chaleur
# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("matrice"):
    ui.titre_carte("Matrice des inégalités territoriales",
                   f"{min(top_n, len(t))} {niveau_lib.lower()}s au rang moyen le plus défavorable. Couleur = rang centile parmi les "
                   f"{len(t)} {niveau_lib.lower()}s du périmètre (1 = moins bien desservi) ; texte = valeur observée.")
    cols = [c for c in I.INDICATEURS_SOUS_DESSERTE if f"rang_{c}" in t]
    if len(t) < 3 or not cols:
        ui.vide("Au moins trois territoires sont nécessaires pour calculer des rangs comparables.", titre="Données insuffisantes")
    else:
        m = t.sort_values("score", ascending=False).head(top_n)
        noms = [f"{r.territoire}" + (f" ({r.prefecture})" if niveau == "commune" else "") for r in m.itertuples()]
        lib_col = {"hab_par_agent": "Hab. / agent MM", "hab_par_etab": "Hab. / établissement", "dist_mediane_km": "Distance médiane",
                   "part_eloignes_pct": f"Agents > {C.SEUIL_ELOIGNEMENT_KM} km", "score": "Rang moyen"}
        rangs = pd.DataFrame({lib_col[c]: m[f"rang_{c}"].values for c in cols}, index=noms)
        rangs[lib_col["score"]] = m.score.values
        txt = pd.DataFrame({lib_col[c]: [("aucun" if (c == "hab_par_etab" and e == 0) else FORMAT[c](v))
                                         for v, e in zip(m[c], m.etablissements)] for c in cols}, index=noms)
        txt[lib_col["score"]] = [nombre(v, 2) for v in m.score]
        hov = pd.DataFrame({k: [f"<b>{n}</b><br>{k} : {x}<br>Rang centile : {nombre(r, 2)}" for n, x, r in zip(noms, txt[k], rangs[k])]
                            for k in rangs.columns}, index=noms)
        ui.graphique(charts.matrice(rangs, txt, hov), "matrice")
        ui.source("Les rangs sont orientés « plus haut = moins bien desservi » ; un territoire sans établissement reçoit le rang le plus "
                  "défavorable pour « habitants par établissement ». Seuils et pondérations : aucune pondération (moyenne simple).")

# --------------------------------------------------------------------------------------
# Éloignement et cantons
# --------------------------------------------------------------------------------------
st.write("")
e1, e2 = st.columns([1.3, 1], gap="medium")
with e1:
    with ui.carte("distance"):
        ui.titre_carte("Éloignement des agents MM au service financier formel",
                       "Distance à vol d'oiseau de chaque agent à l'établissement sélectionné le plus proche.")
        b = I.bandes_distance(ctx.agents_geo)
        if b.empty:
            ui.vide("Aucun agent ou aucun établissement dans la sélection : distance non calculable.")
        else:
            ui.graphique(charts.barres_ordinales(b.bande, b.agents, [f"{entier(a)} · {pct(p, 1)}" for a, p in zip(b.agents, b.part_pct)],
                                                 hauteur=280, couleurs=T.RAMPE_CHAUDE[3:8],
                                                 hover=[f"<b>{r.bande}</b><br>{entier(r.agents)} agents ({pct(r.part_pct)})" for r in b.itertuples()]),
                         "bandes")
            ui.source("Limites : ni réseau routier ni temps de trajet dans les données ; les établissements situés hors du Togo "
                      "(Ghana, Bénin, Burkina Faso) ne sont pas recensés, ce qui peut surestimer l'éloignement en zone frontalière.")
with e2:
    with ui.carte("cantons"):
        ui.titre_carte("Présence au niveau canton", "Comptages sans population (dénominateur non appariable).")
        pc = I.presence_canton(ctx.agents, ctx.finance, f)
        if pc.empty:
            ui.vide("Aucun canton avec point de service dans la sélection.")
        else:
            vc = pc.statut_couverture.value_counts().reindex([I.STATUT_MM_ET_ETAB, I.STATUT_MM_SEUL, I.STATUT_ETAB_SEUL]).fillna(0).astype(int)
            coul = {I.STATUT_MM_ET_ETAB: T.GREEN_700, I.STATUT_MM_SEUL: T.CRITIQUE, I.STATUT_ETAB_SEUL: T.NEUTRE}
            ui.graphique(charts.barres_h(["MM + établissement", "MM seul", "Établissement seul"], vc.values,
                                         [coul[k] for k in vc.index], hauteur=190,
                                         texte=[f"{entier(v)} · {pct(100 * v / vc.sum(), 0)}" for v in vc.values],
                                         hover=[f"<b>{k}</b><br>{entier(v)} cantons" for k, v in vc.items()]), "cantons_bar")
            ui.source(f"{entier(len(pc))} cantons contiennent au moins un point de service. Un canton absent des deux fichiers "
                      "est invisible : l'univers des cantons sans aucun point n'est pas observable.")
            ui.telecharger(pc.rename(columns={"region": "Région", "prefecture": "Préfecture", "commune": "Commune", "canton": "Canton",
                                              "agents": "Agents MM", "etablissements": "Établissements",
                                              "statut_couverture": "Situation observée"}), "presence_cantons")

# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("table_inclusion"):
    ui.titre_carte(f"Indicateurs par {niveau_lib.lower()}", "Toutes les valeurs, triées selon le critère choisi — téléchargeables.")
    cols = ["territoire", "region"] + (["prefecture"] if niveau == "commune" else []) + [
        "population", "agents", "etablissements", "hab_par_agent", "hab_par_etab", "agents_10k", "etab_100k", "agents_par_etab",
        "dist_mediane_km", "part_eloignes_pct", "score", "statut_couverture"]
    tab = t_rank[cols].rename(columns={"territoire": niveau_lib, "region": "Région", "prefecture": "Préfecture",
                                       **{k: I.LIBELLES.get(k, k) for k in cols[2:]}, "statut_couverture": "Situation observée"})
    st.dataframe(tab, hide_index=True, width="stretch", height=380, column_config={
        I.LIBELLES["population"]: st.column_config.NumberColumn(format="localized"),
        I.LIBELLES["hab_par_agent"]: st.column_config.NumberColumn(format="%.0f"),
        I.LIBELLES["hab_par_etab"]: st.column_config.NumberColumn(format="%.0f"),
        I.LIBELLES["agents_10k"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["etab_100k"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["agents_par_etab"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["dist_mediane_km"]: st.column_config.NumberColumn(format="%.2f"),
        I.LIBELLES["part_eloignes_pct"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["score"]: st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)})
    ui.telecharger(tab, f"inclusion_{niveau}")

ui.encadre("<b>Absence dans les données ≠ absence réelle du service.</b> « Aucun établissement observé » signifie qu'aucun "
           "établissement n'est recensé dans le fichier fourni pour ce territoire ; un point non collecté, une agence ouverte "
           "après la collecte ou un service itinérant restent possibles. Cette distinction n'est pas démontrable avec les données disponibles.",
           "warn", "alert")
