"""Composants d'interface (HTML/CSS) réutilisés par toutes les pages.

Principe : l'information d'abord. Pas d'icône décorative ; les précisions méthodologiques
passent dans une infobulle (« i ») plutôt que dans des paragraphes.
"""
from __future__ import annotations

import html
from contextlib import contextmanager

import pandas as pd
import streamlit as st

from . import config as C


def esc(x) -> str:
    return html.escape(str(x))


def injecter_css() -> None:
    css = (C.ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def info(texte: str) -> str:
    """Pastille « i » dont l'infobulle porte la source ou la formule."""
    return f'<span class="info" title="{esc(texte)}">i</span>' if texte else ""


def entete(titre: str, lede: str = "", filtres: list[tuple[str, str, bool]] | None = None) -> None:
    """filtres : (libellé, valeur, appliqué ?) — seuls les filtres appliqués sont rappelés."""
    f = ""
    actifs = [(l, v) for l, v, on in (filtres or []) if on]
    if actifs:
        f = '<div class="filtres">' + "".join(f"<span>{esc(l)} <b>{esc(v)}</b></span>" for l, v in actifs) + "</div>"
    st.html(f'<div class="page-head"><h1>{esc(titre)}</h1>'
            f'{"<p class=lede>" + lede + "</p>" if lede else ""}{f}</div>')


def kpi(label: str, valeur: str, sous: str = "", source: str = "", annee: str = "", icone: str = "",
        ton: str = "", unite: str = "") -> str:
    u = f"<small>{esc(unite)}</small>" if unite else ""
    pied = " · ".join(x for x in [f"<b>{esc(annee)}</b>" if annee and annee not in ("—", "n.d.") else "", esc(source)] if x)
    return (f'<div class="kpi {"alert" if ton == "alert" else ""}"><div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-value">{esc(valeur)}{u}</div><div class="kpi-sub">{sous}</div>'
            f'<div class="kpi-foot">{pied}</div></div>')


def rangee_kpi(cartes: list[str]) -> None:
    cols = st.columns(len(cartes), gap="small")
    for c, h in zip(cols, cartes):
        with c:
            st.html(h)


def constat(titre: str, texte: str = "", icone: str = "", ton: str = "") -> str:
    return (f'<div class="insight {ton}"><div class="t">{titre}</div>'
            f'{"<div class=d>" + texte + "</div>" if texte else ""}</div>')


def encadre(texte: str, ton: str = "", icone: str = "") -> None:
    st.html(f'<div class="callout {"alert" if ton == "alert" else ""}">{texte}</div>')


def source(texte: str) -> None:
    st.html(f'<div class="src">{texte}</div>')


def note_bas(texte: str) -> None:
    st.html(f'<div class="note-bas">{texte}</div>')


def vide(detail: str = "", titre: str = C.NON_DISPONIBLE) -> None:
    st.html(f'<div class="empty"><div class="t">{esc(titre)}</div>'
            f'{"<div class=d>" + esc(detail) + "</div>" if detail else ""}</div>')


def titre_carte(titre: str, sous: str = "", aide: str = "") -> None:
    st.html(f'<div class="card-title">{esc(titre)}{info(aide)}</div>{"<div class=card-sub>" + sous + "</div>" if sous else ""}')


def titre_section(titre: str, sous: str = "") -> None:
    st.html(f'<div class="section-title">{esc(titre)}</div>{"<div class=section-sub>" + sous + "</div>" if sous else ""}')


@contextmanager
def carte(cle: str):
    with st.container(key=f"card_{cle}"):
        yield


PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines", "zoomIn2d", "zoomOut2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "locale": "fr",
}


def graphique(fig, cle: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG, key=cle)


def telecharger(df: pd.DataFrame, nom: str, libelle: str = "Exporter en CSV", cle: str | None = None) -> None:
    st.download_button(libelle, df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=f"{nom}.csv", mime="text/csv", icon=":material/download:",
                       key=cle or f"dl_{nom}", disabled=df.empty, type="tertiary")
