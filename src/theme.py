"""Jetons de design partagés (tableau de bord et rapport).

Identité verte institutionnelle, contrastée et accessible :
- vert profond #176B57 pour les actions, sélections et chiffres importants (6,2:1 sur le fond) ;
- vert principal #23836A pour la série principale ;
- bleu ardoise #3A5F9E réservé aux séries de comparaison (séparation validée avec le vert : ΔE ≥ 15) ;
- ambre #C7851A pour l'attention (3:1 : toujours accompagné d'une étiquette) ;
- rouge #B7463B réservé aux territoires sans établissement recensé et aux alertes factuelles.
"""
from __future__ import annotations

# Encre et surfaces
INK = "#15211E"
INK_2 = "#62706C"
MUTED = "#7A8783"
BG = "#FAFCFB"
SURFACE = "#FAFCFB"
MENTHE = "#EFF8F4"
LINE = "#D4E8DF"
GRID = "#E6EEEA"
AXIS = "#C3D3CB"
NEUTRE = "#A7B3AE"

# Couleurs d'information (noms historiques conservés pour compatibilité)
VERT_FONCE = "#176B57"
GREEN_700 = "#23836A"   # série principale
INDIGO = "#3A5F9E"      # bleu ardoise : comparaison uniquement
GOLD = "#C7851A"        # ambre : attention
TERRACOTTA = "#4F5E5A"  # barres de classement (encre adoucie)
GREEN_900 = "#15211E"

CATEGORIELLE = [GREEN_700, INDIGO, GOLD]

# Statuts (réservés)
BON = GREEN_700
ALERTE = GOLD
SERIEUX = "#B8643A"
CRITIQUE = "#B7463B"

# Rampes séquentielles (clair → foncé)
RAMPE_CHAUDE = ["#EEF3F1", "#D7E1DD", "#BACAC3", "#98ADA5", "#768E86", "#566E67", "#3A504A", "#22332F"]
RAMPE_VERTE = ["#EFF8F4", "#D2EADF", "#ACD6C4", "#7FBEA5", "#4FA285", "#23836A", "#176B57", "#0F4F40"]
RAMPE_SABLE = ["#F4F8F6", "#E6EEEA", "#D6E1DC", "#C3D1CB", "#AFC0B9", "#99ACA4"]
ORDINALE_VERTE = ["#7FBEA5", "#23836A", "#0F4F40"]  # 2G → 3G → 4G

OPERATEURS = {"Togocom": GREEN_700, "Moov": INDIGO, "Moov + Togocom": GOLD, "Togocom seul": GREEN_700,
              "Moov seul": INDIGO, "Non renseigné": NEUTRE, "Marché": INK_2, "Non précisé": NEUTRE}
CATEGORIES_FIN = {"Banque": TERRACOTTA, "Micro-finance": TERRACOTTA, "Mutuelle": TERRACOTTA, "Assurance": TERRACOTTA}
CATEGORIES_CARTE = {"Banque": GREEN_700, "Micro-finance et mutuelles": GOLD, "Assurance": INDIGO}

PHASES = {"Accélération": GREEN_700, "Rythme constant": "#7FBEA5", "Progression ralentie": "#BFDDD0",
          "Stagnation": "#C3D3CB", "Recul": CRITIQUE, "—": "#C3D3CB"}

FONT = "'Public Sans', 'Segoe UI', system-ui, -apple-system, sans-serif"
