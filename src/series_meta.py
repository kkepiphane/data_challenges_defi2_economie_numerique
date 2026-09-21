"""Métadonnées des séries télécoms : libellés, familles, opérateurs, unités.

Les valeurs ne sont jamais modifiées ici ; seuls les libellés sont clarifiés et
les unités manifestement erronées signalées. Correspondance nominative entre raisons
sociales et marques : Togo Cellulaire → Togocom (mobile), Togo Telecom → Togocom (fixe),
Atlantique Telecom → Moov. Cette correspondance n'introduit aucune valeur.
"""
from __future__ import annotations

from .config import SRC_TELECOM_INTERNET, SRC_TELECOM_MARCHE

# famille, libellé, groupe opérateur, opérateur (raison sociale), technologie, unité, statut qualité
_I = SRC_TELECOM_INTERNET
_M = SRC_TELECOM_MARCHE

META = {
    # --- Abonnés Internet (agrégats) ---------------------------------------------------
    "T abonnés Internet Fixe et Mobile (Toutes technologies)": (_I, "Internet — abonnés", "Abonnés Internet fixe + mobile", "Marché", "Ensemble du marché", "Toutes", "abonnés", "ok"),
    "T abonnés Internet haut débit Fixe et Mobile": (_I, "Internet — abonnés", "Abonnés Internet haut débit fixe + mobile", "Marché", "Ensemble du marché", "Haut débit", "abonnés", "ok"),
    "T abonnés Internet mobiles (Toutes technologies)": (_I, "Internet — abonnés", "Abonnés Internet mobile (toutes technologies)", "Marché", "Ensemble du marché", "Mobile", "abonnés", "ok"),
    "T abonnés Internet mobiles (Haut débit)": (_I, "Internet — abonnés", "Abonnés Internet mobile haut débit (3G + 4G)", "Marché", "Ensemble du marché", "Mobile haut débit", "abonnés", "ok"),
    # --- Internet mobile par opérateur et technologie ------------------------------------
    "Abonnés GPRS /EDGE Togo Cellulaire": (_I, "Internet mobile — technologie", "Abonnés 2G (GPRS/EDGE) — Togocom", "Togocom", "Togo Cellulaire", "2G (GPRS/EDGE)", "abonnés", "ok"),
    "Abonnés GPRS/EDGE Atlantique Telecom": (_I, "Internet mobile — technologie", "Abonnés 2G (GPRS/EDGE) — Moov", "Moov", "Atlantique Telecom", "2G (GPRS/EDGE)", "abonnés", "ok"),
    "Nombre de clients 3G Togo Cellulaire": (_I, "Internet mobile — technologie", "Clients 3G — Togocom", "Togocom", "Togo Cellulaire", "3G", "abonnés", "ok"),
    "Nombre de clients 3G Atlantique Telecom": (_I, "Internet mobile — technologie", "Clients 3G — Moov", "Moov", "Atlantique Telecom", "3G", "abonnés", "ok"),
    "Nombre de clients 4G Togo Cellulaire": (_I, "Internet mobile — technologie", "Clients 4G — Togocom", "Togocom", "Togo Cellulaire", "4G", "abonnés", "ok"),
    "Nombre de clients 4G Atlantique Telecom": (_I, "Internet mobile — technologie", "Clients 4G — Moov", "Moov", "Atlantique Telecom", "4G", "abonnés", "serie_incomplete"),
    "T Togo Cellulaire": (_I, "Internet mobile — opérateur", "Abonnés Internet mobile — Togocom", "Togocom", "Togo Cellulaire", "Mobile", "abonnés", "ok"),
    "T Atlantique Telecom": (_I, "Internet mobile — opérateur", "Abonnés Internet mobile — Moov", "Moov", "Atlantique Telecom", "Mobile", "abonnés", "ok"),
    # --- Internet fixe --------------------------------------------------------------------
    "T Abonnés Internet Togo Telecom": (_I, "Internet fixe", "Abonnés Internet fixe — Togo Telecom", "Togocom", "Togo Telecom", "Fixe", "abonnés", "ok"),
    "ADSL": (_I, "Internet fixe — technologie", "ADSL", "Non précisé", "Non précisé", "ADSL", "abonnés", "ok"),
    "FTTH": (_I, "Internet fixe — technologie", "Fibre optique (FTTH)", "Non précisé", "Non précisé", "Fibre (FTTH)", "abonnés", "ok"),
    "Wimax": (_I, "Internet fixe — technologie", "WiMAX", "Non précisé", "Non précisé", "WiMAX", "abonnés", "ok"),
    "EvDo": (_I, "Internet fixe — technologie", "EV-DO", "Non précisé", "Non précisé", "EV-DO", "abonnés", "ok"),
    "Illiconet": (_I, "Internet fixe — technologie", "Illiconet", "Non précisé", "Non précisé", "Illiconet", "abonnés", "ok"),
    "Abonnés CAFE": (_I, "Internet fixe — technologie", "Offre « CAFE »", "Non précisé", "Non précisé", "CAFE", "abonnés", "ok"),
    "TEOLIS": (_I, "Internet fixe — technologie", "Offre « TEOLIS »", "Non précisé", "Non précisé", "TEOLIS", "abonnés", "ok"),
    "GVA": (_I, "Internet fixe — technologie", "Offre « GVA »", "Non précisé", "Non précisé", "GVA", "abonnés", "ok"),
    "LS Internet": (_I, "Internet fixe — technologie", "Liaisons spécialisées Internet", "Non précisé", "Non précisé", "LS Internet", "liaisons", "ok"),
    "LS point à point": (_I, "Internet fixe — technologie", "Liaisons spécialisées point à point", "Non précisé", "Non précisé", "LS point à point", "liaisons", "serie_incomplete"),
    # --- Pénétration Internet (unité source « Nombre » erronée : valeurs en %) --------------
    "Taux de pénétration Internet (Toutes technologies) (%)": (_I, "Internet — pénétration", "Taux de pénétration Internet (abonnements, toutes technologies)", "Marché", "Ensemble du marché", "Toutes", "%", "unite_corrigee"),
    "Taux de pénétration Internet haut débit (%)": (_I, "Internet — pénétration", "Taux de pénétration Internet haut débit (abonnements)", "Marché", "Ensemble du marché", "Haut débit", "%", "unite_corrigee"),
    # --- Marché ------------------------------------------------------------------------------
    "Le nombre total d'abonnés fixe et mobile": (_M, "Marché — abonnés", "Abonnés téléphonie fixe + mobile", "Marché", "Ensemble du marché", "Voix", "abonnés", "ok"),
    "Le nombre total d'abonnées mobiles GSM": (_M, "Marché — abonnés", "Abonnés mobiles GSM", "Marché", "Ensemble du marché", "Mobile", "abonnés", "ok"),
    "Le nombre total d'abonnés fixe": (_M, "Marché — abonnés", "Abonnés téléphonie fixe", "Marché", "Ensemble du marché", "Fixe", "abonnés", "ok"),
    "Télédensité fixe": (_M, "Marché — télédensité", "Télédensité fixe", "Marché", "Ensemble du marché", "Fixe", "%", "ok"),
    "Télédensité mobile GSM": (_M, "Marché — télédensité", "Télédensité mobile GSM", "Marché", "Ensemble du marché", "Mobile", "%", "ok"),
    "Chiffres d'Affaires": (_M, "Marché — finances", "Chiffre d'affaires (périmètre non précisé)", "Marché", "Ensemble du marché", "Toutes", "FCFA", "ok"),
    "Investissement": (_M, "Marché — finances", "Investissement (périmètre non précisé)", "Marché", "Ensemble du marché", "Toutes", "FCFA", "ok"),
    "ARPU segment mobile GSM": (_M, "Marché — finances", "ARPU segment mobile GSM", "Marché", "Ensemble du marché", "Mobile", "FCFA", "unite_incoherente"),
    "Part de marché Togo Cellulaire (en abonnées) en %": (_M, "Marché — parts", "Part de marché — Togocom", "Togocom", "Togo Cellulaire", "Mobile", "%", "ok"),
    "Part de marché Atlantique Telecom Togo (en abonnées)": (_M, "Marché — parts", "Part de marché — Moov", "Moov", "Atlantique Telecom", "Mobile", "%", "ok"),
}

COLONNES = ["fichier", "famille", "libelle", "groupe", "operateur_source", "technologie", "unite", "statut_qualite"]

STATUT_QUALITE_LIBELLES = {
    "ok": "Conforme",
    "serie_incomplete": "Série incomplète (années manquantes dans la source)",
    "unite_corrigee": "Unité source « Nombre » incohérente avec le libellé (%) — valeurs inchangées, unité affichée %",
    "unite_incoherente": "Ordre de grandeur incompatible avec l'unité (supérieur au chiffre d'affaires total) — exclu des graphiques",
}
