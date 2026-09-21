"""Recommandations ciblées : générées par règles explicites à partir des indicateurs observés."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, config as C, indicators as I, recommandations as R, theme as T, ui
from src.contexte import contexte, puces_filtres
from src.formatage import entier, km, nombre, pct

ctx = contexte()
f = ctx.f
nat = I.synthese_nationale(ctx.agents, ctx.finance, int(ctx.T["pop_commune"].population.sum()))

niveau_lib = st.session_state.get("niv_reco") or "Commune"
niveau = {"Commune": "commune", "Préfecture": "prefecture"}[niveau_lib]
reco = R.generer(ctx.territoire(niveau), niveau, nat["hab_par_agent"])

n1 = int((reco.priorite == "Priorité 1").sum()) if not reco.empty else 0
ui.entete(
    "06 · Recommandations",
    f"{len(reco)} {niveau_lib.lower()}s ciblées, dont {n1} en priorité 1" if len(reco) else "Aucun territoire ne remplit les critères",
    "Chaque recommandation découle d'au moins un critère mesuré (population, agents, établissements, distances). "
    "Aucun montant, objectif chiffré ni effet économique n'est avancé : l'impact attendu désigne l'indicateur à suivre.",
    puces_filtres(f, periode="sans objet", geo=True, operateur=True, etablissements=True),
)

c1, c2 = st.columns([1, 2], gap="medium", vertical_alignment="bottom")
with c1:
    st.segmented_control("Niveau d'intervention", ["Commune", "Préfecture"], default="Commune", key="niv_reco")
with c2:
    prio_sel = st.pills("Priorités affichées", list(R.PRIORITES.values()), selection_mode="multi",
                        default=list(R.PRIORITES.values()), key="prio_sel")

with st.expander("Critères et règles de priorisation", icon=":material/rule:", expanded=False):
    regles = pd.DataFrame([{"Critère": k, "Libellé": R.CRITERES[k], "Règle de calcul": R.REGLES[k]} for k in R.CRITERES])
    st.dataframe(regles, hide_index=True, width="stretch")
    st.caption(f"Référence nationale d'habitants par agent (mêmes filtres opérateur) : {entier(nat['hab_par_agent'])}. "
               "Priorité = nombre de critères remplis : 3 → priorité 1 ; 2 → priorité 2 ; 1 → priorité 3. "
               "C1 et C4 sont exclusifs (présence ou absence d'établissement).")

if reco.empty:
    ui.vide("Aucun territoire du périmètre ne remplit au moins un critère avec les filtres actuels.", titre="Aucune recommandation")
    st.stop()

r = reco[reco.priorite.isin(prio_sel or [])]
ui.rangee_kpi([
    ui.kpi("Priorité 1", entier((reco.priorite == "Priorité 1").sum()), "3 critères remplis", "Règles C1–C4", "—", "alert", "alert"),
    ui.kpi("Priorité 2", entier((reco.priorite == "Priorité 2").sum()), "2 critères remplis", "Règles C1–C4", "—", "target", "gold"),
    ui.kpi("Priorité 3", entier((reco.priorite == "Priorité 3").sum()), "1 critère rempli", "Règles C1–C4", "—", "info", "indigo"),
    ui.kpi("Population des territoires ciblés", entier(reco.population.sum()),
           f"{pct(100 * reco.population.sum() / max(ctx.pop_total, 1))} de la population du périmètre", "RGPH-5", "2022", "users"),
])
st.write("")

# --------------------------------------------------------------------------------------
if r.empty:
    ui.vide("Aucune recommandation pour les priorités sélectionnées.", titre="Sélection vide")
else:
    ui.titre_section("Territoires prioritaires", "Les six premiers selon le nombre de critères, puis la population concernée.")
    cartes = r.head(6)
    for i in range(0, len(cartes), 3):
        cols = st.columns(3, gap="medium")
        for col, (_, x) in zip(cols, cartes.iloc[i:i + 3].iterrows()):
            p = {"Priorité 1": "p1", "Priorité 2": "p2", "Priorité 3": "p3"}[x.priorite]
            loc = f"{x.prefecture} · {x.region}" if niveau == "commune" else x.region
            with col:
                stats = (f'<div class="reco-stats"><div><b>{entier(x.population)}</b><span>habitants</span></div>'
                         f'<div><b>{entier(x.agents)}</b><span>agents MM</span></div>'
                         f'<div><b>{entier(x.etablissements)}</b><span>établ.</span></div>'
                         f'<div><b>{km(x.dist_mediane_km)}</b><span>dist. méd.</span></div></div>')
                tags = "".join(f"<span>{ui.esc(c)}</span>" for c in x.constats_courts.split(" | "))
                acts = "".join(f"<li>{ui.esc(a)}</li>" for a in x.actions_courtes.split(" | "))
                st.html(
                    f'<div class="reco"><div class="reco-head"><div><div class="reco-terr">{ui.esc(x.territoire)}</div>'
                    f'<div class="reco-loc">{ui.esc(loc)}</div></div><span class="prio {p}">{x.priorite}</span></div>'
                    f'{stats}<div class="reco-row"><span class="k">Constats</span><div class="reco-tags">{tags}</div></div>'
                    f'<div class="reco-row"><span class="k">Actions proposées</span><ul>{acts}</ul></div>'
                    f'<div class="reco-row suivi"><span class="k">Impact attendu</span>Amélioration mesurable de : <b>{ui.esc(x.suivi)}</b> '
                    f'(aucun objectif chiffré).</div></div>')
        st.write("")

# --------------------------------------------------------------------------------------
if niveau == "commune" and not r.empty:
    with ui.carte("concentration_prio"):
        ui.titre_carte("Où se concentrent les communes ciblées", "Nombre de communes ciblées par préfecture, selon la priorité.")
        agg = r.groupby(["prefecture", "priorite"]).size().unstack(fill_value=0)
        agg = agg.reindex(columns=[p for p in ["Priorité 1", "Priorité 2", "Priorité 3"] if p in agg.columns])
        agg = agg.assign(_t=agg.sum(axis=1)).sort_values("_t", ascending=False).drop(columns="_t").head(15)
        fig = go.Figure()
        coul = {"Priorité 1": T.RAMPE_CHAUDE[6], "Priorité 2": T.RAMPE_CHAUDE[4], "Priorité 3": T.RAMPE_CHAUDE[2]}
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
    ui.titre_carte("Toutes les recommandations", "Territoire, problème observé, indicateur source, action proposée et impact attendu.")
    tab = r[["priorite", "territoire", "prefecture", "region", "population", "criteres_libelles", "probleme", "indicateurs",
             "action", "impact", "sources"]].rename(columns={
        "priorite": "Priorité", "territoire": niveau_lib, "prefecture": "Préfecture", "region": "Région", "population": "Population 2022",
        "criteres_libelles": "Critères remplis", "probleme": "Problème observé", "indicateurs": "Indicateurs sources",
        "action": "Action proposée", "impact": "Impact attendu", "sources": "Sources"})
    if niveau == "prefecture":
        tab = tab.drop(columns=["Préfecture"])
    st.dataframe(tab, hide_index=True, width="stretch", height=420,
                 column_config={"Population 2022": st.column_config.NumberColumn(format="localized"),
                                "Problème observé": st.column_config.TextColumn(width="large"),
                                "Action proposée": st.column_config.TextColumn(width="large")})
    ui.telecharger(tab, f"recommandations_{niveau}")

ui.encadre("<b>Portée.</b> Ces recommandations hiérarchisent des territoires à partir de points de service recensés ; "
           "elles ne mesurent ni la demande, ni l'usage effectif du mobile money, ni la rentabilité d'une implantation "
           f"({C.NON_DISPONIBLE.lower()}). Une vérification de terrain est préalable à toute décision d'investissement.",
           "warn", "info")
