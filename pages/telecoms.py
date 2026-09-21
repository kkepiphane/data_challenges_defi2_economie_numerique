"""Marché des télécommunications 2013–2019 : concurrence, technologies, finances du secteur."""
import numpy as np
import pandas as pd
import streamlit as st

from src import charts, config as C, indicators as I, theme as T, ui
from src.contexte import contexte, puces_filtres
from src.formatage import compact, entier, nombre, pct, pp
from src.series_meta import STATUT_QUALITE_LIBELLES

ctx = contexte()
f = ctx.f
tel_all = ctx.T["telecom"]
a0, a1 = max(f.periode[0], 2013), min(f.periode[1], 2019)
ops = list(f.operateurs)

hhi_all = I.hhi_parts(tel_all).set_index("annee")
der_all = hhi_all.iloc[-1]
ui.entete(
    "03 · Marché des télécommunications",
    f"Un duopole serré : Togocom {pct(der_all.Togocom)} – Moov {pct(der_all.Moov)} des abonnés mobiles en {int(hhi_all.index[-1])}",
    "Séries nationales 2013–2019 (dernière année disponible dans les fichiers fournis). Correspondance des raisons sociales : "
    "Togo Cellulaire et Togo Telecom → <b>Togocom</b> ; Atlantique Telecom → <b>Moov</b>.",
    puces_filtres(f, periode=True, operateur=True),
)

if a0 > a1:
    ui.vide(f"La période sélectionnée ({f.periode[0]}–{f.periode[1]}) ne recoupe pas 2013–2019, seule période couverte par les "
            "séries télécoms. Élargissez la période dans la barre latérale.", titre="Aucune donnée télécom sur cette période")
    st.stop()

tel = tel_all[tel_all.annee.between(a0, a1)]
S = lambda k: I.serie(tel, k)
gsm, ca, inv = S("Le nombre total d'abonnées mobiles GSM"), S("Chiffres d'Affaires"), S("Investissement")
hhi = hhi_all.loc[a0:a1]
y = int(gsm.index[-1])

ui.rangee_kpi([
    ui.kpi("Abonnés mobiles GSM", compact(gsm.iloc[-1]),
           f"{pct(100 * (gsm.iloc[-1] / gsm.iloc[0] - 1))} depuis {gsm.index[0]}" if len(gsm) > 1 else "",
           "Séries sectorielles", str(y), "phone"),
    ui.kpi("Chiffre d'affaires du secteur", compact(ca.iloc[-1]), "FCFA · périmètre non précisé dans la source",
           "Séries sectorielles", str(int(ca.index[-1])), "coins", "gold"),
    ui.kpi("Investissement", compact(inv.iloc[-1]), f"soit {pct(100 * inv.iloc[-1] / ca.iloc[-1])} du chiffre d'affaires",
           "Calcul : investissement ÷ CA", str(int(inv.index[-1])), "layers", "indigo"),
    ui.kpi("Concentration (HHI)", entier(hhi.hhi.iloc[-1]), f"Écart entre opérateurs : {nombre(hhi.ecart_pp.iloc[-1])} pts",
           "Σ parts² — 10 000 = monopole", str(int(hhi.index[-1])), "pie", "gold"),
])
st.write("")

onglets = st.tabs(["Concurrence", "Technologies", "Finances du secteur", "Explorateur d'indicateurs"])

# --------------------------------------------------------------------------------------
with onglets[0]:
    c1, c2 = st.columns([1.4, 1], gap="medium")
    with c1:
        with ui.carte("parts"):
            ui.titre_carte("Parts de marché en abonnés mobiles", "Données sources en % ; la somme vaut 100 chaque année (contrôlé).")
            pm = tel[(tel.famille == "Marché — parts") & tel.groupe.isin(ops)]
            if pm.empty:
                ui.vide("Aucun opérateur sélectionné.")
            else:
                ui.graphique(charts.lignes(pm, "annee", "valeur", "groupe", T.OPERATEURS, unite="%", hauteur=330,
                                           format_y=".2f", source="Séries sectorielles (observationdata-mesqyx)"), "pdm")
    with c2:
        with ui.carte("hhi"):
            ui.titre_carte("Indice de concentration HHI", "Calculé à partir des deux parts de marché.")
            h = hhi.reset_index().assign(serie="HHI")
            fig_h = charts.lignes(h, "annee", "hhi", "serie", {"HHI": T.INK_2}, hauteur=330, format_y=",.0f", fmt_fin=entier)
            fig_h.update_yaxes(range=[4990, max(5100, h.hhi.max() + 15)], title_text="HHI (plancher théorique : 5 000)")
            fig_h.update_xaxes(tickvals=list(h.annee[::2]) if len(h) > 4 else list(h.annee))
            ui.graphique(fig_h, "hhi_l")
            ui.source(f"<b>Formule</b> : {I.FORMULES['hhi']}. Avec deux opérateurs, le HHI ne peut descendre sous 5 000 : "
                      "il mesure ici l'écart entre les deux parts.")
    with ui.carte("internet_op"):
        ui.titre_carte("Abonnés à l'Internet mobile par opérateur", "Totaux opérateur (2G + 3G + 4G) — sommes contrôlées.")
        im = tel[(tel.famille == "Internet mobile — opérateur") & tel.groupe.isin(ops)]
        if im.empty:
            ui.vide("Aucun opérateur sélectionné.")
        else:
            ui.graphique(charts.lignes(im.assign(groupe=im.groupe), "annee", "valeur", "groupe", T.OPERATEURS, hauteur=320,
                                       source="Séries sectorielles (observationdata-cxnvmoc)"), "im_op")
            piv = im.pivot_table(index="annee", columns="groupe", values="valeur")
            if {"Togocom", "Moov"} <= set(piv.columns):
                part = 100 * piv.Moov / (piv.Moov + piv.Togocom)
                ui.source(f"Part de Moov dans l'Internet mobile : {pct(part.iloc[0])} en {part.index[0]} → "
                          f"{pct(part.iloc[-1])} en {part.index[-1]} (calcul : abonnés Moov ÷ total des deux opérateurs).")

# --------------------------------------------------------------------------------------
with onglets[1]:
    with ui.carte("techno"):
        ui.titre_carte("Internet mobile par génération technologique", "Abonnés 2G (GPRS/EDGE), 3G et 4G par opérateur.")
        tm = tel[(tel.famille == "Internet mobile — technologie") & tel.groupe.isin(ops)]
        if tm.empty:
            ui.vide("Aucun opérateur sélectionné.")
        else:
            ui.graphique(charts.empile_technologies(tm, [o for o in C.OPERATEURS if o in ops], hauteur=360), "techno")
            manq = []
            if "Moov" in ops:
                ans = set(tm[(tm.groupe == "Moov") & (tm.technologie == "4G")].annee)
                manq = [a for a in range(a0, a1 + 1) if a not in ans]
            if manq:
                ui.encadre(f"<b>4G Moov</b> : série absente de la source pour {', '.join(map(str, manq))} — non estimée. "
                           "Les totaux Moov publiés restent égaux à 2G + 3G ces années-là (contrôle de cohérence).", "warn", "info")
            hd = tm.assign(hd=tm.technologie.isin(["3G", "4G"])).groupby(["groupe", "annee", "hd"]).valeur.sum().unstack()
            if True in hd and False in hd:
                part_hd = (100 * hd[True] / hd.sum(axis=1)).unstack(0)
                ui.source("Part du haut débit (3G + 4G) dans l'Internet mobile, dernière année : " + " · ".join(
                    f"{o} {pct(part_hd[o].dropna().iloc[-1])}" for o in part_hd.columns) + ".")
    c1, c2 = st.columns([1.6, 1], gap="medium")
    with c1:
        with ui.carte("fixe"):
            ui.titre_carte("Internet fixe par technologie et offre", "Échelles propres à chaque panneau ; opérateur non précisé dans la source.")
            fx = tel[tel.famille == "Internet fixe — technologie"]
            ordre = [l for l in ["Fibre optique (FTTH)", "ADSL", "WiMAX", "EV-DO", "Offre « CAFE »", "Offre « GVA »",
                                 "Offre « TEOLIS »", "Liaisons spécialisées Internet"] if l in set(fx.libelle)]
            if fx.empty:
                ui.vide("Aucune donnée d'Internet fixe sur la période.")
            else:
                ui.graphique(charts.multiples(fx, ordre, ncol=4, hauteur=380), "fixe")
    with c2:
        with ui.carte("ftth"):
            ui.titre_carte("Fibre optique (FTTH)", "Abonnés — première année non nulle et dernière année.")
            ft = S("FTTH")
            nz = ft[ft > 0]
            if nz.empty:
                ui.vide("Aucun abonné FTTH sur la période sélectionnée.")
            else:
                st.html(ui.kpi("Abonnés fibre", entier(nz.iloc[-1]), f"contre {entier(nz.iloc[0])} en {nz.index[0]}",
                               "Séries sectorielles", str(int(nz.index[-1])), "signal"))
                fixe_tot = S("T Abonnés Internet Togo Telecom")
                st.write("")
                ui.encadre(f"La fibre ne représente que {pct(100 * nz.iloc[-1] / S('T abonnés Internet Fixe et Mobile (Toutes technologies)').loc[nz.index[-1]], 2)} "
                           f"des abonnements Internet en {nz.index[-1]}. Couverture 3G/4G/fibre par territoire : "
                           f"<b>{C.NON_DISPONIBLE.lower()}</b>.", "", "info")

# --------------------------------------------------------------------------------------
with onglets[2]:
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with ui.carte("ca"):
            ui.titre_carte("Chiffre d'affaires du secteur (FCFA)", "Périmètre (opérateurs, segments) non précisé dans la source.")
            ui.graphique(charts.colonnes(ca.index, ca.values, T.GREEN_700, 300, nom="Chiffre d'affaires", unite_hover="FCFA",
                                         source="observationdata-mesqyx"), "ca")
    with c2:
        with ui.carte("inv"):
            ui.titre_carte("Investissement (FCFA)", "Même source ; non ventilé par opérateur.")
            ui.graphique(charts.colonnes(inv.index, inv.values, T.INDIGO, 300, nom="Investissement", unite_hover="FCFA",
                                         source="observationdata-mesqyx"), "inv")
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        with ui.carte("taux_inv"):
            ui.titre_carte("Taux d'investissement", "Investissement ÷ chiffre d'affaires (%).")
            ti = pd.DataFrame({"annee": ca.index, "valeur": 100 * inv.values / ca.values, "serie": "Taux d'investissement"})
            ti = ti.dropna()
            ui.graphique(charts.lignes(ti, "annee", "valeur", "serie", {"Taux d'investissement": T.INDIGO}, unite="%",
                                       hauteur=280, format_y=".1f"), "ti")
    with c4:
        with ui.carte("ca_abonne"):
            ab = S("Le nombre total d'abonnés fixe et mobile")
            ui.titre_carte("Chiffre d'affaires par abonnement (FCFA / an)", "CA ÷ abonnés fixe + mobile — indicateur dérivé.")
            cpa = ca / ab
            ui.graphique(charts.colonnes(cpa.index, cpa.values, T.GOLD, 280, format_valeur=lambda v: entier(v),
                                         nom="CA par abonnement", unite_hover="FCFA"), "cpa")
    ui.encadre("<b>ARPU exclu.</b> La série « ARPU segment mobile GSM » affiche des valeurs de l'ordre de 3 × 10¹³ FCFA, "
               "supérieures au chiffre d'affaires total du secteur : l'unité déclarée est incohérente. La série est conservée "
               "dans le journal de qualité mais n'est pas représentée.", "warn", "alert")

# --------------------------------------------------------------------------------------
with onglets[3]:
    familles = sorted(tel.famille.unique())
    c1, c2 = st.columns([1, 2], gap="medium")
    with c1:
        fam = st.selectbox("Famille d'indicateurs", familles, index=familles.index("Internet — abonnés") if "Internet — abonnés" in familles else 0,
                           key="exp_famille")
        dispo = tel[(tel.famille == fam) & (tel.groupe.isin(ops + ["Marché", "Non précisé"]))]
        libs = list(dict.fromkeys(dispo.libelle))
        choix = st.multiselect("Indicateurs (4 au plus)", libs, default=libs[:3], key=f"exp_ind_{fam}", max_selections=4,
                               placeholder="Choisir des indicateurs")
    sel = dispo[dispo.libelle.isin(choix)]
    with c2:
        with ui.carte("explorateur"):
            if sel.empty:
                ui.vide("Sélectionnez au moins un indicateur disponible pour les opérateurs choisis.", titre="Aucun indicateur sélectionné")
            elif sel.unite.nunique() > 1:
                ui.vide("Les indicateurs choisis ont des unités différentes : sélectionnez des indicateurs de même unité "
                        "(un seul axe par graphique).", titre="Unités incompatibles")
            else:
                exclus = sel[sel.statut_qualite == "unite_incoherente"]
                sel_g = sel[sel.statut_qualite != "unite_incoherente"]
                if not exclus.empty:
                    ui.encadre("Série exclue du graphique (unité incohérente) : " + ", ".join(exclus.libelle.unique()), "warn", "alert")
                if not sel_g.empty:
                    pal = {l: T.CATEGORIELLE[i % 4] for i, l in enumerate(dict.fromkeys(sel_g.libelle))}
                    ui.graphique(charts.lignes(sel_g, "annee", "valeur", "libelle", pal, unite=sel_g.unite.iloc[0] if sel_g.unite.iloc[0] == "%" else "",
                                               hauteur=340, format_y=",.2f" if sel_g.unite.iloc[0] == "%" else ",.0f"), "explo")
    tab = sel.assign(qualite=sel.statut_qualite.map(STATUT_QUALITE_LIBELLES))[
        ["libelle", "indicateur_source", "groupe", "operateur_source", "technologie", "annee", "valeur", "unite", "fichier", "qualite"]]
    tab.columns = ["Indicateur", "Libellé source", "Opérateur", "Raison sociale", "Technologie", "Année", "Valeur", "Unité", "Fichier", "Qualité"]
    st.dataframe(tab, hide_index=True, width="stretch", height=300,
                 column_config={"Année": st.column_config.NumberColumn(format="%d"),
                                "Valeur": st.column_config.NumberColumn(format="localized")})
    ui.telecharger(tab, f"telecoms_{a0}_{a1}")
