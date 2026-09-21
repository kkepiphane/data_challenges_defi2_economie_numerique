"""Normalisation de libellés pour les appariements."""
from __future__ import annotations

import re
import unicodedata


def cle(texte: str) -> str:
    """Clé d'appariement : sans accents, majuscules, uniquement alphanumérique."""
    s = unicodedata.normalize("NFKD", str(texte)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def numero_final(texte: str) -> int | None:
    """Numéro terminal d'un libellé de commune (« TONE 3 » → 3, « BINAH2 » → 2)."""
    m = re.search(r"(\d+)\s*$", str(texte))
    return int(m.group(1)) if m else None
