"""Services financiers et mobile money : cartographie des points de service."""
import numpy as np
import pandas as pd
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.contexte import contexte, geo, puces_filtres
from src.formatage import entier, nombre, pct

ctx = contexte()
f = ctx.f
ag, fi = ctx.agents_geo, ctx.finance_geo

ui.entete(
    "Services financiers",
    f"{entier(len(ag))} agents mobile money et {entier(len(fi))} établissements financiers, positionnés par GPS.",
    puces_filtres(f, geo=True, operateur=True, etablissements=True),
)

communes_ag = ag.commune.nunique()
communes_fi = fi.commune.nunique()
_pc = ctx.T["pop_commune"].assign(commune=lambda d: d.communes_bdd.str.split("|")).explode("commune")
n_communes = len(I.filtrer_geo(_pc, f))
jr = fi[fi.jours_renseignes]
ui.rangee_kpi([
    ui.kpi("Agents mobile money", entier(len(ag)),
           f"{pct(100 * (ag.classe_operateur == 'Moov + Togocom').mean())} servent les deux opérateurs" if len(ag) else "Aucun dans la sélection",
           "Géoportail PRISE", "2021/22"),
    ui.kpi("Établissements financiers", entier(len(fi)),
           ", ".join(f"{entier(v)} {k.lower()}" for k, v in fi.categorie.value_counts().items()) or "Aucun dans la sélection",
           "Géoportail, extraction 01/2025"),
    ui.kpi("Communes avec établissement", f"{communes_fi}", f"{communes_ag} avec au moins un agent", "Calcul",
           unite=f"sur {n_communes}"),
    ui.kpi("Ouverts le samedi", pct(100 * jr.ouvert_samedi.mean()) if len(jr) else "—",
           "des établissements" if len(jr) else "Jours non renseignés", "Champ etab_jour"),
])
st.write("")

# --------------------------------------------------------------------------------------
with ui.carte("carte_points"):
    h1, h2 = st.columns([1.3, 1], gap="medium", vertical_alignment="bottom")
    with h1:
        vue = st.segmented_control("Affichage", ["Réseau financier", "Opérateurs", "Densité"],
                                   default="Réseau financier", key="vue_carte")
    with h2:
        couches = st.pills("Couches", ["Agents MM", "Établissements", "Population"], selection_mode="multi",
                           default=["Agents MM", "Établissements"], key="couches_carte")
    vue = vue or "Réseau financier"
    couches = couches or []
    gj = geo("prefectures")
    fig = charts.carte(hauteur=640, lat=pd.concat([ag.lat, fi.lat]) if f.geo_actif else None,
                       lon=pd.concat([ag.lon, fi.lon]) if f.geo_actif else None)
    rien = True
    if "Population" in couches:
        if gj is None:
            ui.source("Contours préfectoraux absents : couche population indisponible.")
        else:
            pp_ = ctx.pop["prefecture"]
            per = I.perimetre(f, ctx.pop)["prefecture"]
            pp_ = pp_ if per is None else pp_[pp_.prefecture.isin(per)]
            charts.couche_choroplethe(fig, gj, pp_, "prefecture", "population", "Population 2022", T.RAMPE_SABLE,
                                      [f"<b>{r.prefecture}</b> ({r.region})<br>Population 2022 : {entier(r.population)}"
                                       for r in pp_.itertuples()], opacite=0.6)
            rien = False
    if "Agents MM" in couches and not ag.empty:
        rien = False
        hov = ("<b>Agent MM</b> · " + ag.classe_operateur + "<br>" + ag.commune + " — " + ag.canton + "<br>Établissement le plus proche : "
               + ag.dist_min_km.map(lambda v: f"{nombre(v, 1)} km" if pd.notna(v) else "—")).tolist()
        if vue == "Densité":
            charts.couche_densite(fig, ag, rayon=8)
        elif vue == "Opérateurs":
            for cl in C.OP_CLASSES:
                sub = ag[ag.classe_operateur == cl]
                if not sub.empty:
                    charts.couche_points(fig, sub, f"{cl} ({entier(len(sub))})", T.OPERATEURS[cl], 5, 0.75,
                                         [h for h, m in zip(hov, ag.classe_operateur == cl) if m])
        else:
            charts.couche_points(fig, ag, f"Agents MM ({entier(len(ag))})", "#8A8A84", 4, 0.35, hov)
    if "Établissements" in couches and not fi.empty and vue != "Opérateurs":
        rien = False
        carte_cat = fi.categorie.replace({"Micro-finance": "Micro-finance et mutuelles", "Mutuelle": "Micro-finance et mutuelles"})
        for cat, coul in T.CATEGORIES_CARTE.items():
            sub = fi[carte_cat == cat]
            if sub.empty:
                continue
            hov = ("<b>" + sub.nom + "</b><br>" + sub.categorie + " · statut : " + sub.statut_source + "<br>" + sub.localite
                   + ", " + sub.commune + "<br>Ouverture : " + sub.jours_ouverture).tolist()
            charts.couche_points(fig, sub, f"{cat} ({entier(len(sub))})", coul, 9, 0.95, hov)
    if rien:
        ui.vide("Activez une couche ou élargissez les filtres.", titre="Carte vide")
    else:
        ui.graphique(fig, "carte_services")
    ui.source("Agents : géoportail PRISE 2021/22. Établissements : géoportail, extraction 01/2025. "
              + ("En vue « Opérateurs », les établissements sont masqués." if vue == "Opérateurs" else ""))

# --------------------------------------------------------------------------------------
st.write("")
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    with ui.carte("cat"):
        ui.titre_carte("Par catégorie", aide="Établissements, selon la catégorie déclarée dans la source.")
        if fi.empty:
            ui.vide("Aucun établissement dans la sélection.")
        else:
            vc = fi.categorie.value_counts().reindex([c for c in C.FIN_CATEGORIES if c in f.categories]).fillna(0)
            ui.graphique(charts.barres_h(vc.index, vc.values, texte=[entier(v) for v in vc.values], hauteur=240,
                                         hover=[f"<b>{k}</b><br>{entier(v)} établissements" for k, v in vc.items()]), "bar_cat")
with c2:
    with ui.carte("ops"):
        ui.titre_carte("Par opérateur", aide="Agents mobile money selon l'opérateur servi ; un agent peut servir les deux.")
        if ag.empty:
            ui.vide("Aucun agent dans la sélection.")
        else:
            vc = ag.classe_operateur.value_counts().reindex(C.OP_CLASSES).dropna()
            ui.graphique(charts.barres_h(vc.index, vc.values, texte=[entier(v) for v in vc.values], hauteur=240,
                                         hover=[f"<b>{k}</b><br>{entier(v)} agents" for k, v in vc.items()]), "bar_ops")
with c3:
    with ui.carte("jours"):
        ui.titre_carte("Ouverture le samedi", aide="Part des établissements dont les jours d'ouverture sont renseignés. Horaires : non disponibles.")
        if jr.empty:
            ui.vide("Jours d'ouverture non renseignés.")
        else:
            d = (jr.assign(samedi=np.where(jr.ouvert_samedi, "Ouvert", "Fermé"))
                   .groupby(["categorie", "samedi"]).size().rename("n").reset_index())
            ui.graphique(charts.barres_100(d, "categorie", "samedi", "n", {"Ouvert": T.INK_2, "Fermé": "#DADAD5"},
                                           ["Ouvert", "Fermé"], hauteur=240), "bar_jours")

# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("repartition"):
    ui.titre_carte("Répartition territoriale", aide="Comptages bruts. Les ratios par habitant figurent dans « Inclusion territoriale ».")
    niv = st.segmented_control("Niveau", ["Région", "Préfecture", "Commune", "Canton"], default="Préfecture",
                               key="niv_repartition", label_visibility="collapsed")
    niv = niv or "Préfecture"
    col = {"Région": "region", "Préfecture": "prefecture", "Commune": "commune", "Canton": "canton"}[niv]
    cles = ["region", "prefecture", "commune", "canton"][: ["region", "prefecture", "commune", "canton"].index(col) + 1]
    rep = ag.groupby(cles).size().rename("Agents MM").to_frame()
    if not fi.empty:
        rep = rep.join(fi.pivot_table(index=cles, columns="categorie", values="etab_id", aggfunc="size", fill_value=0), how="outer")
    rep = rep.fillna(0).astype(int).reset_index()
    if not rep.empty:
        cats = [c for c in C.FIN_CATEGORIES if c in rep.columns]
        rep["Établissements"] = rep[cats].sum(axis=1) if cats else 0
        rep = rep.rename(columns={"region": "Région", "prefecture": "Préfecture", "commune": "Commune", "canton": "Canton"})
        rep = rep.sort_values("Agents MM", ascending=False)
        st.dataframe(rep, hide_index=True, width="stretch", height=360,
                     column_config={"Agents MM": st.column_config.ProgressColumn(color="#A3A39D", format="%d", min_value=0, max_value=int(rep["Agents MM"].max() or 1))})
        if niv == "Canton":
            ui.source("Seuls les cantons contenant au moins un point apparaissent.")
        ui.telecharger(rep, f"repartition_{col}")
    else:
        ui.vide("Aucun point de service dans la sélection.")

st.write("")
t1, t2 = st.tabs(["Établissements", "Agents mobile money"])
with t1:
    tf = fi[["nom", "categorie", "statut_source", "statut_groupe", "region", "prefecture", "commune", "canton", "localite",
             "jours_ouverture", "lat", "lon"]].rename(columns={
        "nom": "Nom", "categorie": "Catégorie", "statut_source": "Statut (source)", "statut_groupe": "Statut (regroupé)",
        "region": "Région", "prefecture": "Préfecture", "commune": "Commune", "canton": "Canton", "localite": "Localité",
        "jours_ouverture": "Jours d'ouverture", "lat": "Latitude", "lon": "Longitude"})
    recherche = st.text_input("Rechercher", placeholder="Nom, localité ou commune", key="recherche_etab")
    if recherche:
        m = tf[["Nom", "Localité", "Commune"]].apply(lambda s: s.str.contains(recherche, case=False, na=False)).any(axis=1)
        tf = tf[m]
    if tf.empty:
        ui.vide("Aucun établissement ne correspond.", titre="Aucun résultat")
    else:
        st.dataframe(tf, hide_index=True, width="stretch", height=320)
    ui.telecharger(tf, "etablissements_financiers_filtres")
with t2:
    ta = ag[["agent_id", "classe_operateur", "operateur_source", "region", "prefecture", "commune", "canton", "dist_min_km",
             "lat", "lon"]].rename(columns={
        "agent_id": "Identifiant (FID)", "classe_operateur": "Opérateurs servis", "operateur_source": "Opérateur (source)",
        "region": "Région", "prefecture": "Préfecture", "commune": "Commune", "canton": "Canton",
        "dist_min_km": "Établissement le plus proche (km)", "lat": "Latitude", "lon": "Longitude"})
    ui.source(f"{entier(len(ta))} agents : aperçu des 500 premiers, export complet.")
    st.dataframe(ta.head(500), hide_index=True, width="stretch", height=320,
                 column_config={"Établissement le plus proche (km)": st.column_config.NumberColumn(format="%.2f")})
    ui.telecharger(ta, "agents_mobile_money_filtres")

ui.note_bas("<b>Rattachements.</b> Région, préfecture et commune sont celles déclarées dans la source "
            "(concordantes avec la position GPS pour 98,4 % des agents et 99,2 % des établissements).")
