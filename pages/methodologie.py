"""Fiche méthodologique : sources, définitions, jointures, contrôles, dictionnaire et limites."""
import pandas as pd
import streamlit as st

from src import config as C, indicators as I, recommandations as R, ui
from src.contexte import contexte

ctx = contexte()
T = ctx.T
ctrl = T["controles"]

ui.entete(
    "Référence",
    "Méthodologie, sources et qualité des données",
    f"Chaque chiffre du tableau de bord se retrace jusqu'à un fichier de <code>data/</code> et une formule. "
    f"{len(ctrl)} contrôles automatiques sont rejoués à chaque exécution du pipeline ({(ctrl.resultat == 'OK').sum()} conformes, "
    f"{(ctrl.resultat != 'OK').sum()} écarts documentés).",
)

onglets = st.tabs(["Sources", "Définitions & formules", "Jointures", "Contrôles", "Journal de qualité",
                   "Dictionnaire de données", "Champs absents", "Analyses impossibles"])

with onglets[0]:
    src = pd.DataFrame([{"Fichier": k, "Contenu": v["titre"], "Producteur": v["producteur"], "Période": v["periode"],
                         "Granularité": v["granularite"]} for k, v in C.SOURCES.items()])
    st.dataframe(src, hide_index=True, width="stretch")
    ui.encadre("<b>Donnée issue du Défi 1</b> (seule donnée externe à <code>data/</code>, faute de géométrie surfacique dans les "
               "fichiers fournis) : contours préfectoraux COD-AB OCHA (valides au 07/01/2021), déjà réconciliés avec les noms PRISE "
               "(<code>defi1/data/processed/prefectures.gpkg</code>). Ils servent uniquement à cartographier et à contrôler la "
               "cohérence spatiale ; les agrégations utilisent les rattachements déclarés dans les sources. La période de collecte "
               "des agents (PRISE 2021/2022) provient de l'audit du catalogue du géoportail réalisé au Défi 1 "
               "(<code>defi1/reports/audit_sources.md</code>) ; les 19 788 agents fournis ici y sont identiques, enregistrement par enregistrement.",
               "", "database")

with onglets[1]:
    defs = pd.DataFrame([{"Indicateur": I.LIBELLES.get(k, k), "Formule / définition": v} for k, v in I.FORMULES.items()])
    st.dataframe(defs, hide_index=True, width="stretch")
    st.markdown(f"""
- **Établissement financier** : enregistrement du fichier établissements (un point de service physique). Catégories : banque, micro-finance, mutuelle, assurance (déclarées). Par défaut, le tableau de bord retient les **établissements de dépôt et de crédit** (banques, micro-finance, mutuelles) ; les assurances sont activables. Le nombre de guichets par établissement n'est pas disponible.
- **Statut** : « En activité » = Utilisé ; « Déclaré non opérationnel » = Fermé, En construction, Inachevé, Abandonné, En réfection, Sans local ; les autres valeurs (Néant, Nsp, N/a, Autre, Location) sont « non renseigné ou ambigu ». Par défaut : en activité + non renseigné.
- **Agent mobile money** : point de service du fichier agents. « Moov, Togocom » = agent servant les deux opérateurs ; « Nsp » = opérateur non renseigné.
- **Distance** : grand cercle (haversine) entre un agent et l'établissement sélectionné le plus proche ; pas de temps de trajet.
- **Rang moyen de sous-desserte** : moyenne simple de rangs centiles ; synthèse descriptive, sans pondération ni prétention causale.
- **Phases de l'usage d'Internet** : seuils modifiables dans la page ; recul (< −seuil), stagnation (|Δ| ≤ seuil), accélération (Δ > Δ précédente + tolérance), rythme constant, progression ralentie.
- **Recommandations** : critères C1–C4 ci-dessous ; priorité = nombre de critères remplis.
""")
    st.dataframe(pd.DataFrame([{"Critère": k, "Libellé": R.CRITERES[k], "Règle": R.REGLES[k]} for k in R.CRITERES]),
                 hide_index=True, width="stretch")

with onglets[2]:
    joints = pd.DataFrame([
        {"Jointure": "Agents / établissements ↔ population (région, préfecture)", "Clé": "Noms normalisés (sans accents) + alias « TOTOAL AVE » → Avé",
         "Statut": "Réalisée", "Couverture": "5/5 régions · 39/39 préfectures", "Justification": "Hiérarchie RGPH-5 reconstruite par sommes exactes ; Grand Lomé (DAGL) rattaché à Maritime comme dans PRISE"},
        {"Jointure": "Agents / établissements ↔ population (commune)", "Clé": "Rang de la commune dans sa préfecture, contrôlé par le numéro du libellé",
         "Statut": "Réalisée", "Couverture": "117 communes → 116 unités", "Justification": "Danyi 1 + Danyi 2 fusionnées dans la source ; 2 libellés corrigés (Amou 3, Est-Mono 3) ; « BINAH2 » normalisé"},
        {"Jointure": "Agents / établissements ↔ population (canton)", "Clé": "Nom de canton",
         "Statut": "Non réalisée", "Couverture": "Appariement partiel, non fiable", "Justification": "Orthographes divergentes (Komah / Sokodè (Komah)…), cantons RGPH absents de PRISE, quartiers du Grand Lomé ≠ cantons PRISE"},
        {"Jointure": "Agents ↔ établissements (distance)", "Clé": "Coordonnées GPS", "Statut": "Réalisée",
         "Couverture": "19 788 agents × 738 établissements", "Justification": "Plus proche voisin (BallTree haversine) par catégorie × statut"},
        {"Jointure": "Points ↔ contours préfectoraux", "Clé": "Point dans polygone", "Statut": "Contrôle uniquement",
         "Couverture": "98,4 % (agents) · 99,2 % (établissements) concordants", "Justification": "Écarts en limite de préfecture ; l'attribut déclaré fait foi"},
        {"Jointure": "Séries télécoms ↔ agents mobile money", "Clé": "Opérateur", "Statut": "Correspondance nominative seulement",
         "Couverture": "Togo Cellulaire / Togo Telecom → Togocom ; Atlantique Telecom → Moov", "Justification": "Périodes disjointes (2013–2019 / 2021–22) : aucun ratio croisé calculé"},
        {"Jointure": "Usage d'Internet ↔ territoires", "Clé": "—", "Statut": "Impossible",
         "Couverture": "—", "Justification": "Séries nationales uniquement"},
    ])
    st.dataframe(joints, hide_index=True, width="stretch")

with onglets[3]:
    vue = st.segmented_control("Afficher", ["Tous", "Écarts seulement"], default="Tous", key="ctrl_vue")
    c = ctrl if vue != "Écarts seulement" else ctrl[ctrl.resultat != "OK"]
    st.dataframe(c.rename(columns={"domaine": "Domaine", "controle": "Contrôle", "resultat": "Résultat", "detail": "Détail"}),
                 hide_index=True, width="stretch", height=520)
    ui.telecharger(ctrl, "controles_qualite")

with onglets[4]:
    j = T["journal"].rename(columns={"fichier": "Fichier", "lignes": "Lignes", "doublons": "Doublons", "couverture_temporelle": "Couverture temporelle",
                                     "couverture_geographique": "Couverture géographique", "valeurs_non_informatives": "Valeurs non informatives",
                                     "limites": "Limites"})
    st.dataframe(j, hide_index=True, width="stretch")
    ui.telecharger(j, "journal_qualite")

with onglets[5]:
    d = T["dictionnaire"]
    fichier = st.selectbox("Fichier", d.fichier.unique(), key="dico_fichier")
    st.dataframe(d[d.fichier == fichier].drop(columns=["fichier"]), hide_index=True, width="stretch")
    ui.telecharger(d, "dictionnaire_donnees")

with onglets[6]:
    s = T["schema"]
    for fic, g in s.groupby("fichier_donnees"):
        pres = g.present_dans_les_donnees.sum()
        st.markdown(f"**{fic}** — {pres} champs présents sur {len(g)} décrits dans le schéma")
        st.dataframe(g[~g.present_dans_les_donnees][["no", "champ", "question", "type"]]
                     .rename(columns={"no": "N°", "champ": "Champ absent", "question": "Question", "type": "Type"}),
                     hide_index=True, width="stretch", height=240)

with onglets[7]:
    imp = pd.DataFrame([
        ("Évolution du nombre d'agents ou d'établissements", "Aucune date de collecte individuelle ; une seule extraction par couche"),
        ("Nombre de guichets, de GAB, de clients par établissement", "Champs guichet_nbr, gab_nbr, client_parti… absents du fichier fourni"),
        ("Volumes et types de transactions mobile money, services offerts", "Champs service, transfert_nbr, transfert_international absents"),
        ("Profil des agents (genre, ancienneté)", "Champs agent_genre, agent_annee absents"),
        ("Taux de détention d'un compte (bancaire ou mobile money)", "Aucune enquête ménages ni donnée de comptes dans les sources"),
        ("Usage d'Internet par région, sexe ou âge", "Série Banque mondiale nationale uniquement"),
        ("Couverture réseau 2G/3G/4G/fibre par territoire", "Aucune donnée de couverture ou d'antennes dans les sources"),
        ("Chiffre d'affaires, investissement par opérateur ; ARPU", "Séries nationales seulement ; ARPU d'unité incohérente"),
        ("Séries télécoms après 2019 ; 4G Moov 2018–2019", "Absentes des fichiers fournis"),
        ("Ratios par habitant au niveau canton", "Population cantonale non appariable de façon fiable aux cantons PRISE"),
        ("Cartes choroplèthes communales", "Aucun contour communal dans les sources (ni dans les données du Défi 1)"),
        ("Temps d'accès réel (route) aux services", "Aucun réseau routier ; seules des distances à vol d'oiseau sont calculables"),
        ("Effets causaux (du mobile money sur l'inclusion, du prix sur l'usage…)", "Aucune variable explicative ni dispositif d'identification"),
    ], columns=["Analyse", "Raison"])
    imp["Statut"] = C.NON_DISPONIBLE
    st.dataframe(imp, hide_index=True, width="stretch")
