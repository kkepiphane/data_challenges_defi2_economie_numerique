"""Recommandations ciblées : générées par règles explicites à partir des indicateurs observés."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, config as C, indicators as I, recommandations as R, theme as T, ui
from src.etat import valeur_page
from src.contexte import contexte, puces_filtres
from src.formatage import entier, km, pct

ctx = contexte()
f = ctx.f
nat = I.synthese_nationale(ctx.agents, ctx.finance, int(ctx.T["pop_commune"].population.sum()))

valeur_page("niv_reco", "Commune")
valeur_page("prio_sel", ["Priorité 1", "Priorité 2", "Priorité 3"])
niveau_lib = st.session_state.get("niv_reco") or "Commune"
niveau = {"Commune": "commune", "Préfecture": "prefecture"}[niveau_lib]
reco = R.generer(ctx.territoire(niveau), niveau, nat["hab_par_agent"])

n1 = int((reco.priorite == "Priorité 1").sum()) if not reco.empty else 0
ui.entete(
    "Recommandations",
    f"{len(reco)} {niveau_lib.lower()}s ciblées, dont {n1} en priorité 1. Chaque action découle d'un constat mesuré ; "
    "aucun objectif chiffré n'est avancé." if len(reco) else "Aucun territoire ne remplit les critères.",
    puces_filtres(f, geo=True, operateur=True, etablissements=True),
)

c1, c2, c3 = st.columns([1, 1.6, 1], gap="medium", vertical_alignment="bottom")
with c1:
    st.segmented_control("Niveau", ["Commune", "Préfecture"], key="niv_reco")
with c2:
    prio_sel = st.pills("Priorités", list(R.PRIORITES.values()), selection_mode="multi",
                        key="prio_sel")
with c3:
    with st.popover("Critères", icon=":material/rule:", width="stretch"):
        st.dataframe(pd.DataFrame([{"Critère": k, "Libellé": R.CRITERES[k], "Règle": R.REGLES[k]} for k in R.CRITERES]),
                     hide_index=True, width="stretch")
        st.caption(f"Référence nationale : {entier(nat['hab_par_agent'])} habitants par agent. "
                   "Priorité = nombre de critères remplis (3 → priorité 1).")

if reco.empty:
    ui.vide("Aucun territoire du périmètre ne remplit au moins un critère.", titre="Aucune recommandation")
    st.stop()

r = reco[reco.priorite.isin(prio_sel or [])]
ui.rangee_kpi([
    ui.kpi("Priorité 1", entier((reco.priorite == "Priorité 1").sum()), "3 critères remplis", ton="alert"),
    ui.kpi("Priorité 2", entier((reco.priorite == "Priorité 2").sum()), "2 critères remplis"),
    ui.kpi("Priorité 3", entier((reco.priorite == "Priorité 3").sum()), "1 critère rempli"),
    ui.kpi("Population concernée", entier(reco.population.sum()),
           f"{pct(100 * reco.population.sum() / max(ctx.pop_total, 1))} du périmètre", "RGPH-5", "2022"),
])

# --------------------------------------------------------------------------------------
if r.empty:
    ui.vide("Aucune recommandation pour les priorités choisies.", titre="Sélection vide")
else:
    ui.titre_section("Territoires prioritaires")
    cartes = r.head(6)
    for i in range(0, len(cartes), 3):
        cols = st.columns(3, gap="medium")
        for col, (_, x) in zip(cols, cartes.iloc[i:i + 3].iterrows()):
            p = {"Priorité 1": "p1", "Priorité 2": "p2", "Priorité 3": "p3"}[x.priorite]
            loc = f"{x.prefecture}, {x.region}" if niveau == "commune" else x.region
            stats = (f'<div class="reco-stats"><span><b>{entier(x.population)}</b> hab.</span><span><b>{entier(x.agents)}</b> agents</span>'
                     f'<span><b>{entier(x.etablissements)}</b> établ.</span><span><b>{km(x.dist_mediane_km)}</b> méd.</span></div>')
            constats = "".join(f"<li>{ui.esc(c)}</li>" for c in x.constats_courts.split(" | "))
            actions = "".join(f"<li>{ui.esc(a)}</li>" for a in x.actions_courtes.split(" | "))
            with col:
                st.html(
                    f'<div class="reco"><div class="reco-head"><div><div class="reco-terr">{ui.esc(x.territoire)}</div>'
                    f'<div class="reco-loc">{ui.esc(loc)}</div></div><span class="prio {p}">{x.priorite}</span></div>'
                    f'{stats}<div class="reco-row"><span class="k">Constats</span><ul>{constats}</ul></div>'
                    f'<div class="reco-row"><span class="k">Actions</span><ul>{actions}</ul></div>'
                    f'<div class="reco-row"><span class="k">Indicateur de suivi</span>{ui.esc(x.suivi).capitalize()}</div></div>')
        st.write("")

# --------------------------------------------------------------------------------------
if niveau == "commune" and not r.empty:
    with ui.carte("concentration_prio"):
        ui.titre_carte("Communes ciblées par préfecture")
        agg = r.groupby(["prefecture", "priorite"]).size().unstack(fill_value=0)
        agg = agg.reindex(columns=[p for p in ["Priorité 1", "Priorité 2", "Priorité 3"] if p in agg.columns])
        agg = agg.assign(_t=agg.sum(axis=1)).sort_values("_t", ascending=False).drop(columns="_t").head(15)
        fig = go.Figure()
        coul = {"Priorité 1": T.CRITIQUE, "Priorité 2": "#7A8783", "Priorité 3": "#C3D3CB"}
        for p in agg.columns:
            fig.add_trace(go.Bar(y=agg.index, x=agg[p], name=p, orientation="h", marker_color=coul[p],
                                 marker_line=dict(color="#fff", width=2),
                                 hovertemplate="<b>%{y}</b> · " + p + " : %{x} commune(s)<extra></extra>"))
        charts._base(fig, max(220, 26 * len(agg) + 70), marges=(8, 8, 40, 8))
        fig.update_layout(barmode="stack", bargap=charts._bargap(len(agg), 26 * len(agg), 18), barcornerradius=0)
        fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=T.INK_2, size=12))
        fig.update_xaxes(showgrid=True, gridcolor=T.GRID, dtick=1)
        ui.graphique(fig, "prio_pref")

st.write("")
with ui.carte("table_reco"):
    ui.titre_carte("Liste complète", aide="Sources : RGPH-5 2022, géoportail PRISE 2021/22, géoportail (extraction 01/2025).")
    tab = r[["priorite", "territoire", "prefecture", "region", "population", "criteres_libelles", "probleme", "indicateurs",
             "action", "impact", "sources"]].rename(columns={
        "priorite": "Priorité", "territoire": niveau_lib, "prefecture": "Préfecture", "region": "Région", "population": "Population",
        "criteres_libelles": "Critères remplis", "probleme": "Problème observé", "indicateurs": "Indicateurs",
        "action": "Action proposée", "impact": "Impact attendu", "sources": "Sources"})
    if niveau == "prefecture":
        tab = tab.drop(columns=["Préfecture"])
    st.dataframe(tab, hide_index=True, width="stretch", height=420,
                 column_config={"Population": st.column_config.NumberColumn(format="localized"),
                                "Problème observé": st.column_config.TextColumn(width="large"),
                                "Action proposée": st.column_config.TextColumn(width="large")})
    ui.telecharger(tab, f"recommandations_{niveau}")

ui.note_bas("<b>Portée.</b> Les priorités reposent sur les points de service recensés. Ni la demande, ni l'usage réel du mobile money, "
            "ni la rentabilité ne sont mesurés : une vérification de terrain précède toute décision.")
