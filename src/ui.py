"""Composants d'interface (HTML/CSS) réutilisés par toutes les pages."""
from __future__ import annotations

import html
import urllib.parse
from contextlib import contextmanager

import pandas as pd
import streamlit as st

from . import config as C

# Icônes au trait (24×24), inline pour ne dépendre d'aucune police externe
_P = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
_SVG = {
    "globe": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "signal": f'<svg viewBox="0 0 24 24" {_P}><path d="M2 20h.01M7 20v-4M12 20v-8M17 20V8M22 4v16"/></svg>',
    "users": f'<svg viewBox="0 0 24 24" {_P}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "bank": f'<svg viewBox="0 0 24 24" {_P}><path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/></svg>',
    "phone": f'<svg viewBox="0 0 24 24" {_P}><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/></svg>',
    "pin": f'<svg viewBox="0 0 24 24" {_P}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    "alert": f'<svg viewBox="0 0 24 24" {_P}><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
    "info": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
    "trend": f'<svg viewBox="0 0 24 24" {_P}><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>',
    "layers": f'<svg viewBox="0 0 24 24" {_P}><path d="M12 2 2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>',
    "coins": f'<svg viewBox="0 0 24 24" {_P}><circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18M7 6h1v4M16.71 13.88l.7.71-2.82 2.82"/></svg>',
    "ruler": f'<svg viewBox="0 0 24 24" {_P}><path d="M21.3 8.7 8.7 21.3a1 1 0 0 1-1.4 0l-4.6-4.6a1 1 0 0 1 0-1.4L15.3 2.7a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4z"/><path d="m7.5 10.5 2 2M10.5 7.5l2 2M13.5 4.5l2 2M4.5 13.5l2 2"/></svg>',
    "pie": f'<svg viewBox="0 0 24 24" {_P}><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
    "database": f'<svg viewBox="0 0 24 24" {_P}><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "calendar": f'<svg viewBox="0 0 24 24" {_P}><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
    "off": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/></svg>',
    "target": f'<svg viewBox="0 0 24 24" {_P}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
}


ICONES = {nom: f'<span class="ico ico-{nom}"></span>' for nom in _SVG}


def esc(x) -> str:
    return html.escape(str(x))


def _css_icones() -> str:
    """Les SVG en ligne sont retirés par l'assainisseur HTML de Streamlit : les icônes sont donc
    servies en masques CSS (data URI) et colorées par currentColor."""
    regles = []
    for nom, svg in _SVG.items():
        src = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ').replace("currentColor", "black")
        uri = "data:image/svg+xml," + urllib.parse.quote(src)
        regles.append(f'.ico-{nom}{{-webkit-mask:url("{uri}") center/contain no-repeat;mask:url("{uri}") center/contain no-repeat;}}')
    return ".ico{display:inline-block;width:16px;height:16px;background-color:currentColor;flex:0 0 auto;}" + "".join(regles)


def injecter_css() -> None:
    css = (C.ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    st.html(f"<style>{css}{_css_icones()}</style>")


def entete(eyebrow: str, titre: str, lede: str = "", puces: list[tuple[str, str, bool]] | None = None) -> None:
    """puces : (libellé, valeur, appliqué ?)."""
    ch = ""
    if puces:
        ch = '<div class="chips">' + "".join(
            f'<span class="chip {"on" if on else "off"}">{esc(l)}{" : <b>" + esc(v) + "</b>" if v else ""}</span>'
            for l, v, on in puces) + "</div>"
    st.html(f'<div class="page-head"><div class="eyebrow">{esc(eyebrow)}</div><h1>{esc(titre)}</h1>'
            f'{"<p class=lede>" + lede + "</p>" if lede else ""}{ch}</div>')


def kpi(label: str, valeur: str, sous: str = "", source: str = "", annee: str = "", icone: str = "signal",
        ton: str = "", unite: str = "") -> str:
    u = f"<small>{esc(unite)}</small>" if unite else ""
    yr = f'<span class="yr">{esc(annee)}</span>' if annee else ""
    return (f'<div class="kpi {ton}"><div class="kpi-top"><div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-icon">{ICONES.get(icone, "")}</div></div>'
            f'<div class="kpi-value">{esc(valeur)}{u}</div><div class="kpi-sub">{sous}</div>'
            f'<div class="kpi-foot">{yr}<span>{esc(source)}</span></div></div>')


def rangee_kpi(cartes: list[str]) -> None:
    cols = st.columns(len(cartes), gap="small")
    for c, h in zip(cols, cartes):
        with c:
            st.html(h)


def constat(titre: str, texte: str, icone: str = "info", ton: str = "") -> str:
    return (f'<div class="insight {ton}"><div class="ic">{ICONES.get(icone, "")}</div>'
            f'<div><div class="t">{titre}</div><div class="d">{texte}</div></div></div>')


def encadre(texte: str, ton: str = "", icone: str = "info") -> None:
    st.html(f'<div class="callout {ton}">{ICONES.get(icone, "")}<div>{texte}</div></div>')


def source(texte: str) -> None:
    st.html(f'<div class="src">{texte}</div>')


def vide(detail: str = "", titre: str = C.NON_DISPONIBLE) -> None:
    st.html(f'<div class="empty">{ICONES["off"]}<div class="t">{esc(titre)}</div>'
            f'{"<div class=d>" + esc(detail) + "</div>" if detail else ""}</div>')


def titre_carte(titre: str, sous: str = "") -> None:
    st.html(f'<div class="card-title">{esc(titre)}</div>{"<div class=card-sub>" + sous + "</div>" if sous else ""}')


def titre_section(titre: str, sous: str = "") -> None:
    st.html(f'<div class="section-title">{esc(titre)}</div>{"<div class=section-sub>" + sous + "</div>" if sous else ""}')


@contextmanager
def carte(cle: str):
    with st.container(key=f"card_{cle}"):
        yield


def legende(items: dict[str, str]) -> None:
    st.html('<div class="legend-inline">' + "".join(
        f'<span><i style="background:{c}"></i>{esc(l)}</span>' for l, c in items.items()) + "</div>")


PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "locale": "fr",
}


def graphique(fig, cle: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG, key=cle)


def telecharger(df: pd.DataFrame, nom: str, libelle: str = "Télécharger le tableau (CSV)", cle: str | None = None) -> None:
    st.download_button(libelle, df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=f"{nom}.csv", mime="text/csv", icon=":material/download:",
                       key=cle or f"dl_{nom}", disabled=df.empty)
