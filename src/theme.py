"""Jetons de design partagés (tableau de bord et rapport).

Identité sobre : blanc dominant, encre noire, gris pour la structure. La couleur est réservée à
l'information : trois teintes catégorielles désaturées (validées toutes paires : CVD ΔE ≥ 10,
vision normale ≥ 18, contraste ≥ 3:1) et un rouge réservé aux alertes.
"""
from __future__ import annotations

# Encre et surfaces
INK = "#141414"
INK_2 = "#4A4A47"
MUTED = "#85857F"
BG = "#FFFFFF"
SURFACE = "#FFFFFF"
SUBTLE = "#F6F6F4"
LINE = "#E4E4E0"
GRID = "#EEEEEA"
AXIS = "#C9C9C3"
NEUTRE = "#A3A39D"

# Couleurs d'information (noms conservés pour compatibilité)
GREEN_700 = "#237B52"   # série 1 — vert institutionnel
GOLD = "#B5862A"        # série 2 — ocre
INDIGO = "#4868B0"      # série 3 — bleu ardoise
TERRACOTTA = "#3A3A36"  # barres de classement : encre (la couleur reste réservée à l'alerte)
GREEN_900 = "#141414"

CATEGORIELLE = [GREEN_700, GOLD, INDIGO]

# Statuts (réservés)
BON = GREEN_700
ALERTE = GOLD
SERIEUX = "#B8643A"
CRITIQUE = "#B3312C"

# Rampes séquentielles neutres (clair → foncé)
RAMPE_CHAUDE = ["#F1F1EE", "#DCDCD7", "#C0C0BA", "#9E9E97", "#7A7A73", "#595953", "#3B3B37", "#232320"]
RAMPE_VERTE = ["#EEF4F0", "#D2E3D9", "#AFCDBC", "#86B39A", "#5E9679", "#3D7E5E", "#237B52", "#175A3B"]
RAMPE_SABLE = ["#F7F7F5", "#EDEDEA", "#E0E0DB", "#CFCFC9", "#BABAB3", "#A3A39C"]
ORDINALE_VERTE = ["#9DB5A8", "#5E8A74", "#2E6A52"]  # 2G → 3G → 4G (validée ordinale)

OPERATEURS = {"Togocom": GREEN_700, "Moov": INDIGO, "Moov + Togocom": GOLD, "Togocom seul": GREEN_700,
              "Moov seul": INDIGO, "Non renseigné": NEUTRE, "Marché": INK_2, "Non précisé": NEUTRE}
CATEGORIES_FIN = {"Banque": INK_2, "Micro-finance": INK_2, "Mutuelle": INK_2, "Assurance": INK_2}
CATEGORIES_CARTE = {"Banque": GREEN_700, "Micro-finance et mutuelles": GOLD, "Assurance": INDIGO}

PHASES = {"Accélération": GREEN_700, "Rythme constant": "#8FB3A0", "Progression ralentie": "#C3D6CB",
          "Stagnation": "#C9C9C3", "Recul": CRITIQUE, "—": "#C9C9C3"}

FONT = "'Public Sans', 'Segoe UI', system-ui, -apple-system, sans-serif"
