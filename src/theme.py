"""Jetons de design partagés (tableau de bord et rapport).

Palette catégorielle validée (scripts/validate_palette.js du skill dataviz) :
adjacent CVD ΔE ≥ 19, vision normale ≥ 27 ; sur les cartes (toutes paires) 3 couleurs maximum.
L'or est sous 3:1 sur fond blanc : il est toujours accompagné d'une légende et d'étiquettes.
"""
from __future__ import annotations

INK = "#10231B"
INK_2 = "#4A5A52"
MUTED = "#7D8A83"
BG = "#F5F3EC"
SURFACE = "#FFFFFF"
LINE = "#E4E1D6"
GRID = "#ECEAE2"
AXIS = "#CFCBBE"

GREEN_900 = "#0B2E21"
GREEN_700 = "#1F7A4D"
GOLD = "#E0A100"
INDIGO = "#3B5BA5"
TERRACOTTA = "#C05A2B"
NEUTRE = "#9AA39E"

CATEGORIELLE = [GREEN_700, GOLD, INDIGO, TERRACOTTA]

# Statuts (réservés : jamais utilisés comme couleur de série)
BON = "#0CA30C"
ALERTE = "#FAB219"
SERIEUX = "#EC835A"
CRITIQUE = "#D03B3B"

# Rampes séquentielles (une teinte, clair → foncé)
RAMPE_VERTE = ["#EEF6F1", "#CFE6D8", "#A6D0B7", "#74B38F", "#46956A", "#1F7A4D", "#135A37", "#0B3B24"]
RAMPE_CHAUDE = ["#FBF1EA", "#F6DCCB", "#EEBC9E", "#E29A72", "#D3784C", "#C05A2B", "#98421D", "#6E2E12"]
RAMPE_SABLE = ["#F7F4EC", "#EDE6D5", "#DDD2B8", "#C9BB98", "#B3A279", "#978660"]
ORDINALE_VERTE = ["#74B38F", "#2F8A5B", "#0F4A2E"]  # 2G → 3G → 4G

OPERATEURS = {"Togocom": GREEN_700, "Moov": INDIGO, "Moov + Togocom": GOLD, "Togocom seul": GREEN_700,
              "Moov seul": INDIGO, "Non renseigné": NEUTRE, "Marché": INK_2, "Non précisé": NEUTRE}
CATEGORIES_FIN = {"Banque": GREEN_700, "Micro-finance": GOLD, "Mutuelle": TERRACOTTA, "Assurance": INDIGO}
# Sur carte (toutes paires) : 3 couleurs ; mutuelles regroupées avec la micro-finance (SFD)
CATEGORIES_CARTE = {"Banque": GREEN_700, "Micro-finance et mutuelles": GOLD, "Assurance": INDIGO}

PHASES = {"Accélération": GREEN_700, "Rythme constant": "#74B38F", "Progression ralentie": "#A6D0B7",
          "Stagnation": NEUTRE, "Recul": CRITIQUE, "—": NEUTRE}

FONT = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
