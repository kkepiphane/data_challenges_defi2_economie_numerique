"""Inclusion territoriale : ratios à dénominateur de population de même granularité, classement et inégalités."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.etat import valeur_page
from src.contexte import contexte, geo, puces_filtres
from src.formatage import entier, km, nombre, pct

ctx = contexte()
f = ctx.f

com_all = ctx.territoire("commune")
mm_seul = com_all[com_all.statut_couverture == I.STATUT_MM_SEUL]
ui.entete(
    "Inclusion territoriale",
    (f"{len(mm_seul)} communes ({entier(mm_seul.population.sum())} habitants) n'ont que des agents mobile money, "
     "sans établissement financier recensé." if len(mm_seul) else "Toutes les communes du périmètre comptent un établissement recensé."),
    puces_filtres(f, geo=True, operateur=True, etablissements=True),
)

INDICATEURS = {
    "score": "Rang moyen de sous-desserte",
    "hab_par_etab": "Habitants par établissement",
    "hab_par_agent": "Habitants par agent MM",
    "dist_mediane_km": "Distance médiane au premier établissement",
    "part_eloignes_pct": f"Agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km d'un établissement",
    "agents_par_etab": "Agents MM par établissement",
}
FORMAT = {"score": lambda v: nombre(v, 2), "hab_par_etab": entier, "hab_par_agent": entier, "dist_mediane_km": km,
          "part_eloignes_pct": lambda v: pct(v, 0), "agents_par_etab": lambda v: nombre(v, 1)}

c1, c2, c3 = st.columns([1.3, 1.5, 1], gap="medium", vertical_alignment="bottom")
with c1:
    valeur_page("niv_inclusion", "Préfecture")
    niveau_lib = st.segmented_control("Niveau", ["Région", "Préfecture", "Commune"], key="niv_inclusion")
niveau_lib = niveau_lib or "Préfecture"
niveau = {"Région": "region", "Préfecture": "prefecture", "Commune": "commune"}[niveau_lib]
with c2:
    valeur_page("critere_inclusion", "score")
    critere = st.selectbox("Classer selon", list(INDICATEURS), format_func=INDICATEURS.get, key="critere_inclusion")
t = ctx.territoire(niveau)
with c3:
    if len(t) > 3:
        valeur_page(f"topn_{niveau}_{len(t)}", min(15, len(t)))
        top_n = st.slider("Territoires affichés", 3, min(40, len(t)), key=f"topn_{niveau}_{len(t)}")
    else:
        top_n = len(t)

if t.empty:
    ui.vide("Aucun territoire ne correspond aux filtres.", titre="Aucun territoire")
    st.stop()

nat = I.synthese_nationale(ctx.agents_geo, ctx.finance_geo, ctx.pop_total)
sans = t[(t.etablissements == 0) & (t.agents > 0)]
ui.rangee_kpi([
    ui.kpi("Habitants par agent MM", entier(nat["hab_par_agent"]), f"{entier(nat['agents'])} agents", "RGPH-5 ÷ PRISE", "2022"),
    ui.kpi("Habitants par établissement", entier(nat["hab_par_etab"]), f"{entier(nat['etablissements'])} établissements",
           "RGPH-5 ÷ géoportail", "2022"),
    ui.kpi(f"Agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km", pct(nat["part_eloignes_pct"]),
           f"Distance médiane : {nombre(nat['dist_mediane_km'], 2)} km", "Vol d'oiseau"),
    ui.kpi(f"{niveau_lib}s sans établissement", f"{len(sans)}", f"{entier(sans.population.sum())} habitants", "Calcul",
           ton="alert" if len(sans) else "", unite=f"sur {len(t)}"),
])
st.write("")

# --------------------------------------------------------------------------------------
val = t[critere]
t_rank = t.assign(_v=val.where(~((critere in ("hab_par_etab", "agents_par_etab")) & (t.etablissements == 0)), np.inf))
t_rank = t_rank.sort_values("_v", ascending=False, na_position="last")
g1, g2 = st.columns([1.15, 1], gap="medium")
with g1:
    with ui.carte("carte_inclusion"):
        ui.titre_carte(INDICATEURS[critere],
                       "Plus foncé : moins bien desservi. Rouge : aucun établissement." if niveau != "commune" else
                       "Agents MM ; en rouge, ceux des communes sans établissement.",
                       aide=f"{I.FORMULES.get(critere, '')}. Sources : RGPH-5 2022, PRISE 2021/22, géoportail 01/2025, contours OCHA (Défi 1)."
                            + (" Contours communaux absents : points réels des agents." if niveau == "commune" else ""))
        gj = geo("prefectures" if niveau == "prefecture" else "regions")
        if niveau == "commune":
            ag = ctx.agents_geo.merge(t[["territoire", "statut_couverture"]], left_on="unite_commune", right_on="territoire", how="inner")
            fig = charts.carte(hauteur=560, lat=ag.lat if f.geo_actif else None, lon=ag.lon if f.geo_actif else None)
            for stt, coul, lib, taille, op in [(I.STATUT_MM_ET_ETAB, "#A7B3AE", "Commune avec établissement", 4, 0.35),
                                               (I.STATUT_MM_SEUL, T.CRITIQUE, "Commune sans établissement", 5, 0.9)]:
                sub = ag[ag.statut_couverture == stt]
                if not sub.empty:
                    charts.couche_points(fig, sub, f"{lib} ({entier(len(sub))} agents)", coul, taille, op,
                                         ("<b>" + sub.unite_commune + "</b><br>" + stt + "<br>Établissement le plus proche : "
                                          + sub.dist_min_km.map(km)).tolist())
            fe = ctx.finance_geo
            if not fe.empty:
                charts.couche_points(fig, fe, f"Établissements ({entier(len(fe))})", T.INK, 6, 0.9,
                                     ("<b>" + fe.nom + "</b><br>" + fe.categorie + " · " + fe.commune).tolist())
            ui.graphique(fig, "carte_communes")
        elif gj is None:
            ui.vide("Contours absents : carte indisponible.")
        else:
            cle = "prefecture" if niveau == "prefecture" else "region"
            avec = t[~((critere in ("hab_par_etab", "agents_par_etab")) & (t.etablissements == 0)) & t[critere].notna()]
            fig = charts.carte(hauteur=560)
            if not avec.empty:
                charts.couche_choroplethe(
                    fig, gj, avec.drop(columns=[cle], errors="ignore").rename(columns={"territoire": cle}), cle, critere,
                    INDICATEURS[critere][:28], T.RAMPE_CHAUDE[:7],
                    [f"<b>{r.territoire}</b><br>{INDICATEURS[critere]} : <b>{FORMAT[critere](getattr(r, critere))}</b>"
                     f"<br>Population : {entier(r.population)} · agents : {entier(r.agents)} · établissements : {entier(r.etablissements)}"
                     for r in avec.itertuples()], fmt_barre=",.2f" if critere == "score" else ",.0f")
            vides = t[t.etablissements == 0]
            if not vides.empty:
                fig.add_trace(go.Choroplethmap(
                    geojson=gj, locations=vides.territoire, z=[1] * len(vides), featureidkey=f"properties.{cle}",
                    colorscale=[[0, T.CRITIQUE], [1, T.CRITIQUE]], showscale=False, marker=dict(opacity=0.85, line=dict(color="#fff", width=1)),
                    hovertext=[f"<b>{r.territoire}</b><br>Aucun établissement recensé<br>{entier(r.agents)} agents MM · {entier(r.population)} hab."
                               for r in vides.itertuples()], hovertemplate="%{hovertext}<extra></extra>"))
            if f.geo_actif and not ctx.agents_geo.empty:
                charts.recadrer(fig, ctx.agents_geo.lat, ctx.agents_geo.lon, 560)
            ui.graphique(fig, "carte_inclusion_choro")

with g2:
    with ui.carte("classement"):
        ui.titre_carte(f"Les {min(top_n, len(t_rank))} moins bien desservis",
                       aide=I.FORMULES["score"] + ". Synthèse descriptive, sans pondération." if critere == "score" else I.FORMULES.get(critere, ""))
        sans_crit = t_rank[np.isinf(t_rank._v)]
        if critere in ("hab_par_etab", "agents_par_etab") and not sans_crit.empty:
            ui.encadre(f"<b>Sans établissement ({len(sans_crit)})</b>, placés en tête : "
                       + ", ".join(r.territoire for r in sans_crit.head(10).itertuples())
                       + (" …" if len(sans_crit) > 10 else "") + ".", "alert")
        tr = t_rank[np.isfinite(t_rank._v) & t_rank._v.notna()].head(max(0, top_n - (len(sans_crit) if critere in ("hab_par_etab", "agents_par_etab") else 0)))
        if tr.empty:
            ui.vide("Indicateur non calculable pour les territoires restants.")
        else:
            labels = [f"{r.territoire}" + (f" · {r.prefecture}" if niveau == "commune" else "") for r in tr.itertuples()]
            ui.graphique(charts.barres_h(labels, tr[critere], texte=[FORMAT[critere](v) for v in tr[critere]],
                                         hover=[f"<b>{r.territoire}</b> ({r.region})<br>{INDICATEURS[critere]} : {FORMAT[critere](getattr(r, critere))}"
                                                f"<br>Hab./agent : {entier(r.hab_par_agent)} · Hab./établissement : "
                                                f"{entier(r.hab_par_etab) if r.etablissements else 'aucun'}"
                                                f"<br>Distance médiane : {km(r.dist_mediane_km)} · Agents > {C.SEUIL_ELOIGNEMENT_KM} km : {pct(r.part_eloignes_pct, 0)}"
                                                for r in tr.itertuples()], max_px=18), "classement")

# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("matrice"):
    ui.titre_carte("Matrice des inégalités",
                   f"Les {min(top_n, len(t))} {niveau_lib.lower()}s au rang moyen le plus défavorable.",
                   aide=f"Couleur : rang centile parmi les {len(t)} {niveau_lib.lower()}s (1 = moins bien desservi). "
                        "Texte : valeur observée. Sans établissement : rang le plus défavorable.")
    cols = [c for c in I.INDICATEURS_SOUS_DESSERTE if f"rang_{c}" in t]
    if len(t) < 3 or not cols:
        ui.vide("Au moins trois territoires sont nécessaires.", titre="Données insuffisantes")
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

# --------------------------------------------------------------------------------------
st.write("")
e1, e2 = st.columns([1.3, 1], gap="medium")
with e1:
    with ui.carte("distance"):
        ui.titre_carte("Distance au premier établissement",
                       aide="Distance à vol d'oiseau de chaque agent à l'établissement sélectionné le plus proche. "
                            "Ni réseau routier, ni établissements hors frontière.")
        b = I.bandes_distance(ctx.agents_geo)
        if b.empty:
            ui.vide("Distance non calculable avec la sélection.")
        else:
            ui.graphique(charts.barres_ordinales(b.bande, b.agents, [f"{pct(p, 1)}" for p in b.part_pct],
                                                 hauteur=280, couleurs=T.RAMPE_CHAUDE[2:7],
                                                 hover=[f"<b>{r.bande}</b><br>{entier(r.agents)} agents ({pct(r.part_pct)})" for r in b.itertuples()]),
                         "bandes")
with e2:
    with ui.carte("cantons"):
        ui.titre_carte("Cantons", aide="Comptages sans population : les cantons ne s'apparient pas de façon fiable au recensement. "
                                       "Seuls les cantons contenant au moins un point sont observables.")
        pc = I.presence_canton(ctx.agents, ctx.finance, f)
        if pc.empty:
            ui.vide("Aucun canton avec point de service.")
        else:
            vc = pc.statut_couverture.value_counts().reindex([I.STATUT_MM_ET_ETAB, I.STATUT_MM_SEUL, I.STATUT_ETAB_SEUL]).fillna(0).astype(int)
            coul = {I.STATUT_MM_ET_ETAB: "#7A8783", I.STATUT_MM_SEUL: T.CRITIQUE, I.STATUT_ETAB_SEUL: "#C3D3CB"}
            ui.graphique(charts.barres_h(["Agents et établissement", "Agents seulement", "Établissement seulement"], vc.values,
                                         [coul[k] for k in vc.index], hauteur=190,
                                         texte=[f"{entier(v)} · {pct(100 * v / vc.sum(), 0)}" for v in vc.values],
                                         hover=[f"<b>{k}</b><br>{entier(v)} cantons" for k, v in vc.items()]), "cantons_bar")
            ui.telecharger(pc.rename(columns={"region": "Région", "prefecture": "Préfecture", "commune": "Commune", "canton": "Canton",
                                              "agents": "Agents MM", "etablissements": "Établissements",
                                              "statut_couverture": "Situation observée"}), "presence_cantons")

st.write("")
with ui.carte("table_inclusion"):
    ui.titre_carte(f"Tous les indicateurs par {niveau_lib.lower()}")
    cols = ["territoire"] + (["region"] if niveau != "region" else []) + (["prefecture"] if niveau == "commune" else []) + [
        "population", "agents", "etablissements", "hab_par_agent", "hab_par_etab", "agents_10k", "etab_100k", "agents_par_etab",
        "dist_mediane_km", "part_eloignes_pct", "score", "statut_couverture"]
    tab = t_rank[cols].rename(columns={"territoire": niveau_lib, "region": "Région", "prefecture": "Préfecture",
                                       **{k: I.LIBELLES.get(k, k) for k in cols if k not in ("territoire", "region", "prefecture")},
                                       "statut_couverture": "Situation observée"})
    st.dataframe(tab, hide_index=True, width="stretch", height=380, column_config={
        I.LIBELLES["population"]: st.column_config.NumberColumn(format="localized"),
        I.LIBELLES["hab_par_agent"]: st.column_config.NumberColumn(format="%.0f"),
        I.LIBELLES["hab_par_etab"]: st.column_config.NumberColumn(format="%.0f"),
        I.LIBELLES["agents_10k"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["etab_100k"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["agents_par_etab"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["dist_mediane_km"]: st.column_config.NumberColumn(format="%.2f"),
        I.LIBELLES["part_eloignes_pct"]: st.column_config.NumberColumn(format="%.1f"),
        I.LIBELLES["score"]: st.column_config.ProgressColumn(color="#23836A", format="%.2f", min_value=0, max_value=1)})
    ui.telecharger(tab, f"inclusion_{niveau}")

ui.note_bas("<b>Absence dans les données ≠ absence réelle.</b> « Sans établissement » signifie qu'aucun établissement n'est recensé "
            "dans le fichier fourni. Le canton n'est pas utilisé comme dénominateur (appariement non fiable).")
