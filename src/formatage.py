"""Formatage des nombres à la française (espace fine insécable, virgule décimale)."""
from __future__ import annotations

import math

NNBSP = " "


def _vide(x) -> bool:
    return x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))


def entier(x, defaut: str = "—") -> str:
    if _vide(x):
        return defaut
    return f"{x:,.0f}".replace(",", NNBSP)


def nombre(x, d: int = 1, defaut: str = "—") -> str:
    if _vide(x):
        return defaut
    return f"{x:,.{d}f}".replace(",", NNBSP).replace(".", ",")


def pct(x, d: int = 1, defaut: str = "—") -> str:
    return defaut if _vide(x) else f"{nombre(x, d)}{NNBSP}%"


def pp(x, d: int = 1, defaut: str = "—") -> str:
    if _vide(x):
        return defaut
    signe = "+" if x > 0 else ("−" if x < 0 else "")
    return f"{signe}{nombre(abs(x), d)}{NNBSP}pt{'s' if abs(x) >= 2 else ''}"


def compact(x, unite: str = "", d: int = 1, defaut: str = "—") -> str:
    """6 239 183 → « 6,2 M » ; 184 914 000 000 → « 184,9 Md »."""
    if _vide(x):
        return defaut
    a = abs(x)
    for seuil, suffixe in [(1e9, "Md"), (1e6, "M"), (1e3, "k")]:
        if a >= seuil:
            s = f"{nombre(x / seuil, d)}{NNBSP}{suffixe}"
            break
    else:
        s = entier(x)
    return f"{s}{NNBSP}{unite}".strip() if unite else s


def km(x, d: int = 1) -> str:
    return "—" if _vide(x) else f"{nombre(x, d)}{NNBSP}km"
