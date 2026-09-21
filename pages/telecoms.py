"""Télécommunications 2013–2019 : concurrence, technologies, finances du secteur."""
import pandas as pd
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.contexte import contexte, puces_filtres
from src.formatage import compact, entier, nombre, pct
from src.series_meta import STATUT_QUALITE_LIBELLES

ctx = contexte()
f = ctx.f
tel_all = ctx.T["telecom"]
a0, a1 = max(f.periode[0], 2013), min(f.periode[1], 2019)
ops = list(f.operateurs)

hhi_all = I.hhi_parts(tel_all).set_index("annee")
der_all = hhi_all.iloc[-1]
ui.entete(
    "Télécommunications",
    f"Duopole équilibré en {int(hhi_all.index[-1])} : Togocom {pct(der_all.Togocom)}, Moov {pct(der_all.Moov)} des abonnés mobiles. "
    "Séries disponibles de 2013 à 2019.",
    puces_filtres(f, periode=True, operateur=True),
)

if a0 > a1:
    ui.vide(f"Les séries télécoms couvrent 2013–2019 ; la période choisie ({f.periode[0]}–{f.periode[1]}) n'en recoupe aucune année.",
            titre="Aucune donnée sur cette période")
    st.stop()

tel = tel_all[tel_all.annee.between(a0, a1)]
S = lambda k: I.serie(tel, k)
gsm, ca, inv = S("Le nombre total d'abonnées mobiles GSM"), S("Chiffres d'Affaires"), S("Investissement")
hhi = hhi_all.loc[a0:a1]
SRC = "Séries sectorielles"

ui.rangee_kpi([
    ui.kpi("Abonnés mobiles", compact(gsm.iloc[-1]),
           f"{pct(100 * (gsm.iloc[-1] / gsm.iloc[0] - 1))} depuis {gsm.index[0]}" if len(gsm) > 1 else "", SRC, str(int(gsm.index[-1]))),
    ui.kpi("Chiffre d'affaires", compact(ca.iloc[-1]), "FCFA", SRC, str(int(ca.index[-1]))),
    ui.kpi("Investissement", compact(inv.iloc[-1]), f"{pct(100 * inv.iloc[-1] / ca.iloc[-1])} du chiffre d'affaires",
           SRC, str(int(inv.index[-1]))),
    ui.kpi("Concentration (HHI)", entier(hhi.hhi.iloc[-1]), f"Écart entre opérateurs : {nombre(hhi.ecart_pp.iloc[-1])} pts",
           "Calcul", str(int(hhi.index[-1]))),
])
st.write("")

onglets = st.tabs(["Concurrence", "Technologies", "Finances", "Explorateur"])

# --------------------------------------------------------------------------------------
with onglets[0]:
    c1, c2 = st.columns([1.4, 1], gap="medium")
    with c1:
        with ui.carte("parts"):
            ui.titre_carte("Parts de marché", aide="Parts en abonnés mobiles (%), fichier observationdata-mesqyx. Somme = 100 chaque année.")
            pm = tel[(tel.famille == "Marché — parts") & tel.groupe.isin(ops)]
            if pm.empty:
                ui.vide("Aucun opérateur sélectionné.")
            else:
                ui.graphique(charts.lignes(pm, "annee", "valeur", "groupe", T.OPERATEURS, unite="%", hauteur=330,
                                           format_y=".2f", source=SRC), "pdm")
    with c2:
        with ui.carte("hhi"):
            ui.titre_carte("Indice HHI", aide=f"{I.FORMULES['hhi']}. Avec deux opérateurs, le minimum théorique est 5 000.")
            h = hhi.reset_index().assign(serie="HHI")
            fig_h = charts.lignes(h, "annee", "hhi", "serie", {"HHI": T.INK}, hauteur=330, format_y=",.0f", fmt_fin=entier)
            fig_h.update_yaxes(range=[4990, max(5100, h.hhi.max() + 15)])
            fig_h.update_xaxes(tickvals=list(h.annee[::2]) if len(h) > 4 else list(h.annee))
            ui.graphique(fig_h, "hhi_l")
    with ui.carte("internet_op"):
        ui.titre_carte("Abonnés à l'Internet mobile", aide="Totaux par opérateur (2G + 3G + 4G), fichier observationdata-cxnvmoc.")
        im = tel[(tel.famille == "Internet mobile — opérateur") & tel.groupe.isin(ops)]
        if im.empty:
            ui.vide("Aucun opérateur sélectionné.")
        else:
            ui.graphique(charts.lignes(im, "annee", "valeur", "groupe", T.OPERATEURS, hauteur=320, source=SRC), "im_op")

# --------------------------------------------------------------------------------------
with onglets[1]:
    with ui.carte("techno"):
        ui.titre_carte("Internet mobile par technologie", aide="Abonnés 2G (GPRS/EDGE), 3G et 4G par opérateur.")
        tm = tel[(tel.famille == "Internet mobile — technologie") & tel.groupe.isin(ops)]
        if tm.empty:
            ui.vide("Aucun opérateur sélectionné.")
        else:
            ui.graphique(charts.empile_technologies(tm, [o for o in C.OPERATEURS if o in ops], hauteur=360), "techno")
            manq = []
            if "Moov" in ops:
                ans = set(tm[(tm.groupe == "Moov") & (tm.technologie == "4G")].annee)
                manq = [a for a in range(a0, a1 + 1) if a not in ans]
            hd = tm.assign(hd=tm.technologie.isin(["3G", "4G"])).groupby(["groupe", "annee", "hd"]).valeur.sum().unstack()
            notes = []
            if True in hd and False in hd:
                part_hd = (100 * hd[True] / hd.sum(axis=1)).unstack(0)
                notes.append("Part du haut débit, dernière année : " + ", ".join(
                    f"{o} {pct(part_hd[o].dropna().iloc[-1])}" for o in part_hd.columns) + ".")
            if manq:
                notes.append(f"4G Moov absente de la source pour {', '.join(map(str, manq))}, non estimée.")
            if notes:
                ui.source(" ".join(notes))
    c1, c2 = st.columns([1.6, 1], gap="medium")
    with c1:
        with ui.carte("fixe"):
            ui.titre_carte("Internet fixe", aide="Échelle propre à chaque panneau. Opérateur non précisé dans la source.")
            fx = tel[tel.famille == "Internet fixe — technologie"]
            ordre = [l for l in ["Fibre optique (FTTH)", "ADSL", "WiMAX", "EV-DO", "Offre « CAFE »", "Offre « GVA »",
                                 "Offre « TEOLIS »", "Liaisons spécialisées Internet"] if l in set(fx.libelle)]
            if fx.empty:
                ui.vide("Aucune donnée d'Internet fixe sur la période.")
            else:
                ui.graphique(charts.multiples(fx, ordre, ncol=4, hauteur=380), "fixe")
    with c2:
        with ui.carte("ftth"):
            ui.titre_carte("Fibre optique")
            ft = S("FTTH")
            nz = ft[ft > 0]
            if nz.empty:
                ui.vide("Aucun abonné FTTH sur la période.")
            else:
                total = S("T abonnés Internet Fixe et Mobile (Toutes technologies)").loc[nz.index[-1]]
                st.html(ui.kpi("Abonnés FTTH", entier(nz.iloc[-1]), f"{entier(nz.iloc[0])} en {nz.index[0]}", SRC, str(int(nz.index[-1]))))
                ui.source(f"{pct(100 * nz.iloc[-1] / total, 2)} des abonnements Internet. Couverture territoriale : "
                          f"{C.NON_DISPONIBLE.lower()}.")

# --------------------------------------------------------------------------------------
with onglets[2]:
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with ui.carte("ca"):
            ui.titre_carte("Chiffre d'affaires (FCFA)", aide="Périmètre (opérateurs, segments) non précisé dans la source.")
            ui.graphique(charts.colonnes(ca.index, ca.values, hauteur=300, nom="Chiffre d'affaires", unite_hover="FCFA", source=SRC), "ca")
    with c2:
        with ui.carte("inv"):
            ui.titre_carte("Investissement (FCFA)", aide="Non ventilé par opérateur.")
            ui.graphique(charts.colonnes(inv.index, inv.values, hauteur=300, nom="Investissement", unite_hover="FCFA", source=SRC), "inv")
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        with ui.carte("taux_inv"):
            ui.titre_carte("Taux d'investissement", aide="Investissement ÷ chiffre d'affaires.")
            ti = pd.DataFrame({"annee": ca.index, "valeur": 100 * inv.values / ca.values, "serie": "Taux d'investissement"}).dropna()
            ui.graphique(charts.lignes(ti, "annee", "valeur", "serie", {"Taux d'investissement": T.INK}, unite="%",
                                       hauteur=280, format_y=".1f"), "ti")
    with c4:
        with ui.carte("ca_abonne"):
            ab = S("Le nombre total d'abonnés fixe et mobile")
            ui.titre_carte("Chiffre d'affaires par abonnement (FCFA / an)", aide="CA ÷ abonnés fixe et mobile.")
            cpa = ca / ab
            ui.graphique(charts.colonnes(cpa.index, cpa.values, hauteur=280, format_valeur=lambda v: entier(v),
                                         nom="CA par abonnement", unite_hover="FCFA"), "cpa")
    ui.source("L'ARPU publié (≈ 3 × 10¹³ FCFA, supérieur au chiffre d'affaires total) a une unité incohérente : il n'est pas représenté.")

# --------------------------------------------------------------------------------------
with onglets[3]:
    familles = sorted(tel.famille.unique())
    c1, c2 = st.columns([1, 2], gap="medium")
    with c1:
        fam = st.selectbox("Famille", familles, index=familles.index("Internet — abonnés") if "Internet — abonnés" in familles else 0,
                           key="exp_famille")
        dispo = tel[(tel.famille == fam) & (tel.groupe.isin(ops + ["Marché", "Non précisé"]))]
        libs = list(dict.fromkeys(dispo.libelle))
        choix = st.multiselect("Indicateurs (4 au plus)", libs, default=libs[:3], key=f"exp_ind_{fam}", max_selections=4,
                               placeholder="Choisir")
    sel = dispo[dispo.libelle.isin(choix)]
    with c2:
        with ui.carte("explorateur"):
            if sel.empty:
                ui.vide("Choisissez au moins un indicateur.", titre="Aucun indicateur sélectionné")
            elif sel.unite.nunique() > 1:
                ui.vide("Choisissez des indicateurs de même unité.", titre="Unités incompatibles")
            else:
                exclus = sel[sel.statut_qualite == "unite_incoherente"]
                sel_g = sel[sel.statut_qualite != "unite_incoherente"]
                if not exclus.empty:
                    ui.source("Non représenté (unité incohérente) : " + ", ".join(exclus.libelle.unique()) + ".")
                if not sel_g.empty:
                    pal = {l: T.CATEGORIELLE[i % 3] if len(set(sel_g.libelle)) > 1 else T.INK
                           for i, l in enumerate(dict.fromkeys(sel_g.libelle))}
                    u = sel_g.unite.iloc[0]
                    ui.graphique(charts.lignes(sel_g, "annee", "valeur", "libelle", pal, unite=u if u == "%" else "",
                                               hauteur=340, format_y=",.2f" if u == "%" else ",.0f"), "explo")
    tab = sel.assign(qualite=sel.statut_qualite.map(STATUT_QUALITE_LIBELLES))[
        ["libelle", "indicateur_source", "groupe", "operateur_source", "technologie", "annee", "valeur", "unite", "fichier", "qualite"]]
    tab.columns = ["Indicateur", "Libellé source", "Opérateur", "Raison sociale", "Technologie", "Année", "Valeur", "Unité", "Fichier", "Qualité"]
    st.dataframe(tab, hide_index=True, width="stretch", height=300,
                 column_config={"Année": st.column_config.NumberColumn(format="%d"),
                                "Valeur": st.column_config.NumberColumn(format="localized")})
    ui.telecharger(tab, f"telecoms_{a0}_{a1}")

ui.note_bas("<b>Opérateurs.</b> Togo Cellulaire et Togo Telecom correspondent à Togocom ; Atlantique Telecom à Moov. "
            "Producteur des séries non indiqué dans les fichiers.")
