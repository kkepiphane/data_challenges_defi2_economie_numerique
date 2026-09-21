"""Accès aux services financiers et mobile money : cartographie des points de service."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.contexte import contexte, geo, puces_filtres
from src.formatage import entier, nombre, pct

ctx = contexte()
f = ctx.f
ag, fi = ctx.agents_geo, ctx.finance_geo

ui.entete(
    "04 · Services financiers & mobile money",
    f"{entier(len(ag))} agents mobile money et {entier(len(fi))} établissements financiers géolocalisés",
    f"Périmètre : <b>{f.libelle_geo()}</b>. Chaque point est une position GPS réelle issue du géoportail ; les rattachements "
    "administratifs sont ceux déclarés dans la source (concordants avec la géométrie pour 98,4 % des agents et 99,2 % des établissements).",
    puces_filtres(f, periode="sans objet — aucune date de collecte individuelle", geo=True, operateur=True, etablissements=True),
)

communes_ag = ag.commune.nunique()
communes_fi = fi.commune.nunique()
_pc = ctx.T["pop_commune"].assign(commune=lambda d: d.communes_bdd.str.split("|")).explode("commune")
n_communes = len(I.filtrer_geo(_pc, f))
jr = fi[fi.jours_renseignes]
ui.rangee_kpi([
    ui.kpi("Agents mobile money", entier(len(ag)),
           f"{pct(100 * (ag.classe_operateur == 'Moov + Togocom').mean())} servent les deux opérateurs" if len(ag) else "Aucun agent dans la sélection",
           "Géoportail PRISE", "2021/22", "phone"),
    ui.kpi("Établissements financiers", entier(len(fi)),
           " · ".join(f"{entier(v)} {k.lower()}" for k, v in fi.categorie.value_counts().items()) or "Aucun établissement dans la sélection",
           "Géoportail (extraction 01/2025)", "n.d.", "bank", "indigo"),
    ui.kpi("Communes avec établissement", f"{communes_fi}", f"contre {communes_ag} communes avec au moins un agent MM",
           "Communes PRISE du périmètre", "—", "pin", "gold", unite=f"/ {n_communes}"),
    ui.kpi("Ouverts le samedi", pct(100 * jr.ouvert_samedi.mean()) if len(jr) else "—",
           f"{entier(len(jr))} établissements aux jours d'ouverture renseignés" if len(jr) else "Jours d'ouverture non renseignés",
           "Champ etab_jour", "n.d.", "calendar", "indigo"),
])
st.write("")

# --------------------------------------------------------------------------------------
# Carte
# --------------------------------------------------------------------------------------
with ui.carte("carte_points"):
    h1, h2, h3 = st.columns([1.4, 1, 1], gap="small", vertical_alignment="bottom")
    with h1:
        vue = st.segmented_control("Vue cartographique", ["Réseau financier", "Agents par opérateur", "Densité d'agents"],
                                   default="Réseau financier", key="vue_carte")
    with h2:
        couches = st.pills("Couches", ["Agents MM", "Établissements", "Population"], selection_mode="multi",
                           default=["Agents MM", "Établissements"], key="couches_carte")
    with h3:
        fond_pop = "Population" in (couches or [])
        st.caption("Population : choroplèthe préfectorale (RGPH-5 2022). Contours : COD-AB OCHA (Défi 1).")
    vue = vue or "Réseau financier"
    couches = couches or []
    gj = geo("prefectures")
    fig = charts.carte(hauteur=640, lat=pd.concat([ag.lat, fi.lat]) if f.geo_actif else None,
                       lon=pd.concat([ag.lon, fi.lon]) if f.geo_actif else None)
    rien = True
    if fond_pop:
        if gj is None:
            ui.encadre("Contours préfectoraux absents : couche population indisponible.", "warn", "alert")
        else:
            pp_ = ctx.pop["prefecture"]
            per = I.perimetre(f, ctx.pop)["prefecture"]
            pp_ = pp_ if per is None else pp_[pp_.prefecture.isin(per)]
            charts.couche_choroplethe(fig, gj, pp_, "prefecture", "population", "Population 2022", T.RAMPE_SABLE,
                                      [f"<b>{r.prefecture}</b> ({r.region})<br>Population 2022 : {entier(r.population)}"
                                       for r in pp_.itertuples()], opacite=0.55)
            rien = False
    if "Agents MM" in couches and not ag.empty:
        rien = False
        hov = ("<b>Agent MM</b> · " + ag.classe_operateur + "<br>" + ag.commune + " — " + ag.canton + "<br>Établissement le plus proche : "
               + ag.dist_min_km.map(lambda v: f"{nombre(v, 1)} km" if pd.notna(v) else "—")).tolist()
        if vue == "Densité d'agents":
            charts.couche_densite(fig, ag, rayon=8)
        elif vue == "Agents par opérateur":
            for cl in C.OP_CLASSES:
                sub = ag[ag.classe_operateur == cl]
                if not sub.empty:
                    charts.couche_points(fig, sub, f"{cl} ({entier(len(sub))})", T.OPERATEURS[cl], 5, 0.75,
                                         [h for h, m in zip(hov, ag.classe_operateur == cl) if m])
        else:
            charts.couche_points(fig, ag, f"Agents MM ({entier(len(ag))})", "#4F5B55", 4, 0.35, hov)
    if "Établissements" in couches and not fi.empty and vue != "Agents par opérateur":
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
        ui.vide("Aucune couche à afficher : activez une couche ou élargissez les filtres.", titre="Carte vide")
    else:
        ui.graphique(fig, "carte_services")
    notes = ["<b>Sources</b> : agents (géoportail PRISE 2021/22, extraction 19/12/2024) · établissements (géoportail, extraction 08/01/2025)."]
    if vue == "Agents par opérateur" and "Établissements" in couches:
        notes.append("Vue opérateurs : établissements masqués pour limiter la carte à trois couleurs distinctes.")
    notes.append("Sur la carte, micro-finance et mutuelles partagent une couleur ; les graphiques ci-dessous les distinguent.")
    ui.source(" ".join(notes))

# --------------------------------------------------------------------------------------
# Répartitions
# --------------------------------------------------------------------------------------
st.write("")
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    with ui.carte("cat"):
        ui.titre_carte("Établissements par catégorie", "Catégorie déclarée dans la source.")
        if fi.empty:
            ui.vide("Aucun établissement dans la sélection.")
        else:
            vc = fi.categorie.value_counts().reindex([c for c in C.FIN_CATEGORIES if c in f.categories]).fillna(0)
            ui.graphique(charts.barres_h(vc.index, vc.values, [T.CATEGORIES_FIN[c] for c in vc.index],
                                         texte=[f"{entier(v)} · {pct(100 * v / vc.sum(), 0)}" for v in vc.values],
                                         hover=[f"<b>{k}</b><br>{entier(v)} établissements" for k, v in vc.items()]), "bar_cat")
            st_vc = fi.statut_groupe.value_counts()
            ui.source("Statuts : " + " · ".join(f"{k} {entier(v)}" for k, v in st_vc.items()))
with c2:
    with ui.carte("ops"):
        ui.titre_carte("Agents MM par opérateur servi", "Un agent peut servir les deux opérateurs.")
        if ag.empty:
            ui.vide("Aucun agent dans la sélection.")
        else:
            vc = ag.classe_operateur.value_counts().reindex(C.OP_CLASSES).dropna()
            ui.graphique(charts.barres_h(vc.index, vc.values, [T.OPERATEURS[c] for c in vc.index],
                                         texte=[f"{entier(v)} · {pct(100 * v / vc.sum(), 0)}" for v in vc.values],
                                         hover=[f"<b>{k}</b><br>{entier(v)} agents" for k, v in vc.items()]), "bar_ops")
            ui.source(f"Agents accessibles aux clients Togocom : {entier(ag.sert_togocom.sum())} · Moov : {entier(ag.sert_moov.sum())}.")
with c3:
    with ui.carte("jours"):
        ui.titre_carte("Ouverture le samedi, par catégorie", "Part des établissements aux jours renseignés.")
        if jr.empty:
            ui.vide("Jours d'ouverture non renseignés dans la sélection.")
        else:
            d = (jr.assign(samedi=np.where(jr.ouvert_samedi, "Ouvert le samedi", "Fermé le samedi"))
                   .groupby(["categorie", "samedi"]).size().rename("n").reset_index())
            ui.graphique(charts.barres_100(d, "categorie", "samedi", "n",
                                           {"Ouvert le samedi": T.GREEN_700, "Fermé le samedi": "#CFD6D2"},
                                           ["Ouvert le samedi", "Fermé le samedi"], hauteur=240), "bar_jours")
            ui.source(f"Ouverts le dimanche : {entier(jr.ouvert_dimanche.sum())} établissement(s). Horaires : champ absent des données.")

# --------------------------------------------------------------------------------------
# Répartition territoriale et tables
# --------------------------------------------------------------------------------------
st.write("")
with ui.carte("repartition"):
    ui.titre_carte("Répartition territoriale des points de service", "Comptages bruts ; les ratios par habitant sont dans « Inclusion territoriale ».")
    niv = st.segmented_control("Niveau", ["Région", "Préfecture", "Commune", "Canton"], default="Préfecture", key="niv_repartition")
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
                     column_config={"Agents MM": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=int(rep["Agents MM"].max() or 1))})
        if niv == "Canton":
            ui.source("Canton : seuls les cantons contenant au moins un point apparaissent (la liste exhaustive des cantons n'est pas fournie).")
        ui.telecharger(rep, f"repartition_{col}")
    else:
        ui.vide("Aucun point de service dans la sélection.")

t1, t2 = st.tabs(["Établissements financiers", "Agents mobile money"])
with t1:
    tf = fi[["nom", "categorie", "statut_source", "statut_groupe", "region", "prefecture", "commune", "canton", "localite",
             "jours_ouverture", "lat", "lon"]].rename(columns={
        "nom": "Nom", "categorie": "Catégorie", "statut_source": "Statut (source)", "statut_groupe": "Statut (regroupé)",
        "region": "Région", "prefecture": "Préfecture", "commune": "Commune", "canton": "Canton", "localite": "Localité",
        "jours_ouverture": "Jours d'ouverture", "lat": "Latitude", "lon": "Longitude"})
    recherche = st.text_input("Rechercher un établissement", placeholder="Nom, localité ou commune…", key="recherche_etab")
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
    st.caption(f"{entier(len(ta))} agents — aperçu des 500 premiers ; le téléchargement contient la sélection complète.")
    st.dataframe(ta.head(500), hide_index=True, width="stretch", height=320,
                 column_config={"Établissement le plus proche (km)": st.column_config.NumberColumn(format="%.2f")})
    ui.telecharger(ta, "agents_mobile_money_filtres")
