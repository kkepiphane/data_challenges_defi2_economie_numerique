"""Fabriques de graphiques Plotly (charte unique : traits fins, grille discrète, infobulles en français)."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import theme as T
from .formatage import compact, entier, nombre

CENTRE_TOGO = {"lat": 8.62, "lon": 0.95}
STYLE_CARTE = "carto-positron"


def _base(fig: go.Figure, hauteur: int = 360, legende: bool = True, marges=(8, 8, 36, 8)) -> go.Figure:
    g, d, h, b = marges
    fig.update_layout(
        height=hauteur, margin=dict(l=g, r=d, t=h, b=b),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=T.FONT, size=12, color=T.INK_2),
        separators=", ",
        hoverlabel=dict(bgcolor=T.SURFACE, bordercolor=T.LINE, font=dict(family=T.FONT, size=12, color=T.INK), align="left"),
        showlegend=legende,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title=None,
                    font=dict(size=12, color=T.INK_2), bgcolor="rgba(0,0,0,0)", itemclick="toggle"),
        barcornerradius=4,
    )
    fig.update_xaxes(showgrid=False, linecolor=T.AXIS, linewidth=1, ticks="", tickfont=dict(color=T.MUTED),
                     title_font=dict(color=T.MUTED, size=11), zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=T.GRID, gridwidth=1, linecolor="rgba(0,0,0,0)", ticks="",
                     tickfont=dict(color=T.MUTED), title_font=dict(color=T.MUTED, size=11), zeroline=False)
    return fig


def _bargap(n: int, hauteur_trace: float, max_px: float = 22) -> float:
    if n <= 0:
        return 0.3
    return float(min(0.85, max(0.25, 1 - max_px / (hauteur_trace / n))))


# ======================================================================================
# Séries temporelles
# ======================================================================================
def courbe_internet(d: pd.DataFrame, comparaison: pd.DataFrame | None = None, hauteur: int = 400) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d.annee, y=d.valeur_pct, mode="lines+markers", name="Individus utilisant Internet (BM/UIT)",
        line=dict(color=T.INK, width=2.25, shape="linear"),
        marker=dict(size=6, color=T.INK, line=dict(color=T.SURFACE, width=1.5)),
        fill="tozeroy", fillcolor="rgba(20,20,20,0.04)",
        customdata=np.c_[d.variation_pp.fillna(np.nan), d.phase],
        hovertemplate="<b>%{x}</b><br>Individus utilisant Internet : <b>%{y:.1f} %</b>"
                      "<br>Variation : %{customdata[0]:+.1f} pt<br>Phase : %{customdata[1]}"
                      "<br><span style='color:#7D8A83'>Source : Banque mondiale (WDI/UIT)</span><extra></extra>"))
    if comparaison is not None and not comparaison.empty:
        for (lib, g), coul in zip(comparaison.groupby("libelle", sort=False), [T.GOLD, T.INDIGO]):
            fig.add_trace(go.Scatter(
                x=g.annee, y=g.valeur, mode="lines+markers", name=lib, line=dict(color=coul, width=2),
                marker=dict(size=7, color=coul, line=dict(color=T.SURFACE, width=2)),
                hovertemplate=f"<b>%{{x}}</b><br>{lib} : <b>%{{y:.1f}} %</b>"
                              "<br><span style='color:#7D8A83'>Source : séries sectorielles 2013–2019</span><extra></extra>"))
    if not d.empty:
        der = d.iloc[-1]
        fig.add_annotation(x=der.annee, y=der.valeur_pct, text=f"<b>{nombre(der.valeur_pct)} %</b><br>{int(der.annee)}",
                           showarrow=False, xanchor="left", xshift=10, yshift=4, font=dict(color=T.INK, size=12), align="left")
    _base(fig, hauteur, legende=comparaison is not None and not comparaison.empty, marges=(8, 70, 40, 8))
    fig.update_yaxes(ticksuffix=" %", rangemode="tozero")
    fig.update_xaxes(dtick=2 if len(d) > 14 else 1)
    fig.update_layout(hovermode="closest")
    return fig


def barres_variation(d: pd.DataFrame, hauteur: int = 300) -> go.Figure:
    d = d.dropna(subset=["variation_pp"])
    fig = go.Figure()
    for phase, coul in T.PHASES.items():
        g = d[d.phase == phase]
        if g.empty:
            continue
        fig.add_trace(go.Bar(
            x=g.annee, y=g.variation_pp, name=phase, marker_color=coul, width=0.62,
            customdata=np.c_[g.valeur_pct, g.croissance_pct],
            hovertemplate="<b>%{x}</b> · " + phase + "<br>Variation : <b>%{y:+.2f} pt</b>"
                          "<br>Niveau : %{customdata[0]:.1f} %<br>Croissance relative : %{customdata[1]:+.1f} %<extra></extra>"))
    _base(fig, hauteur, marges=(8, 8, 40, 8))
    fig.update_layout(barmode="overlay")
    fig.update_yaxes(ticksuffix=" pt", zeroline=True, zerolinecolor=T.AXIS)
    fig.update_xaxes(dtick=2 if len(d) > 14 else 1)
    return fig


def lignes(df: pd.DataFrame, x: str, y: str, groupe: str, couleurs: dict[str, str], unite: str = "",
           hauteur: int = 320, etiquettes_fin: bool = True, format_y: str = ",.0f", source: str = "",
           fmt_fin=None) -> go.Figure:
    fig = go.Figure()
    for g, sub in df.groupby(groupe, sort=False):
        sub = sub.sort_values(x)
        coul = couleurs.get(g, T.INK_2)
        fig.add_trace(go.Scatter(
            x=sub[x], y=sub[y], name=str(g), mode="lines+markers",
            line=dict(color=coul, width=2), marker=dict(size=7, color=coul, line=dict(color=T.SURFACE, width=2)),
            hovertemplate=f"<b>{g}</b> · %{{x}}<br>%{{y:{format_y}}} {unite}"
                          + (f"<br><span style='color:#7D8A83'>{source}</span>" if source else "") + "<extra></extra>"))
        if etiquettes_fin and len(sub):
            v = sub[y].iloc[-1]
            txt = fmt_fin(v) if fmt_fin else (f"{nombre(v, 1)} {unite}".strip() if unite == "%" else compact(v))
            fig.add_annotation(x=sub[x].iloc[-1], y=v, text=f"<b>{txt}</b>", showarrow=False, xanchor="left", xshift=8,
                               font=dict(color=T.INK, size=11))
    _base(fig, hauteur, legende=df[groupe].nunique() > 1, marges=(8, 64, 40 if df[groupe].nunique() > 1 else 16, 8))
    fig.update_xaxes(dtick=1)
    if pd.api.types.is_numeric_dtype(df[x]) and len(df):
        fig.update_xaxes(range=[df[x].min() - 0.3, df[x].max() + 0.3])
    if unite == "%":
        fig.update_yaxes(ticksuffix=" %")
    fig.update_layout(hovermode="x unified" if df[groupe].nunique() > 1 else "closest")
    return fig


def colonnes(x, y, couleur: str = T.INK_2, hauteur: int = 300, format_valeur=compact, nom: str = "",
             unite_hover: str = "", source: str = "") -> go.Figure:
    x, y = list(x), list(y)
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=couleur, name=nom,
        text=[format_valeur(v) for v in y], textposition="outside", cliponaxis=False, constraintext="none",
        textfont=dict(color=T.INK_2, size=11),
        hovertemplate=f"<b>%{{x}}</b><br>{nom} : <b>%{{y:,.0f}} {unite_hover}</b>"
                      + (f"<br><span style='color:#7D8A83'>{source}</span>" if source else "") + "<extra></extra>"))
    _base(fig, hauteur, legende=False, marges=(8, 8, 24, 8))
    fig.update_layout(bargap=_bargap(len(x), 900, 26))
    fig.update_xaxes(dtick=1, type="category")
    fig.update_yaxes(showticklabels=False, showgrid=False, rangemode="tozero")
    return fig


def empile_technologies(df: pd.DataFrame, operateurs: list[str], hauteur: int = 330) -> go.Figure:
    """Colonnes empilées 2G/3G/4G par opérateur (petits multiples)."""
    techs = ["2G (GPRS/EDGE)", "3G", "4G"]
    fig = make_subplots(rows=1, cols=len(operateurs), shared_yaxes=True, subplot_titles=operateurs, horizontal_spacing=0.06)
    for j, op in enumerate(operateurs, start=1):
        sub = df[df.groupe == op]
        for tech, coul in zip(techs, T.ORDINALE_VERTE):
            g = sub[sub.technologie == tech].sort_values("annee")
            fig.add_trace(go.Bar(
                x=g.annee, y=g.valeur, name=tech, marker_color=coul, showlegend=j == 1, legendgroup=tech,
                marker_line=dict(color=T.SURFACE, width=1.5),
                hovertemplate=f"<b>{op} · {tech}</b> · %{{x}}<br>%{{y:,.0f}} abonnés<extra></extra>"), row=1, col=j)
    _base(fig, hauteur, marges=(8, 8, 56, 8))
    fig.update_layout(barmode="stack", bargap=0.35)
    fig.update_xaxes(dtick=1)
    for a in fig.layout.annotations:
        a.update(font=dict(size=12, color=T.INK), xanchor="left", x=a.x - 0.2 if len(operateurs) > 1 else 0)
    fig.update_layout(legend=dict(y=1.12))
    return fig


def multiples(df: pd.DataFrame, ordre: list[str], ncol: int = 4, hauteur: int = 380, couleur: str = T.INK) -> go.Figure:
    n = len(ordre)
    nrow = math.ceil(n / ncol)
    courts = [o.replace("Liaisons spécialisées Internet", "LS Internet").replace("Fibre optique (FTTH)", "Fibre (FTTH)") for o in ordre]
    fig = make_subplots(rows=nrow, cols=ncol, subplot_titles=courts, vertical_spacing=0.2, horizontal_spacing=0.07)
    for i, lib in enumerate(ordre):
        r, c = i // ncol + 1, i % ncol + 1
        g = df[df.libelle == lib].sort_values("annee")
        fig.add_trace(go.Scatter(x=g.annee, y=g.valeur, mode="lines+markers", line=dict(color=couleur, width=2),
                                 marker=dict(size=6, color=couleur, line=dict(color=T.SURFACE, width=1.5)),
                                 fill="tozeroy", fillcolor="rgba(20,20,20,0.04)",
                                 hovertemplate=f"<b>{lib}</b> · %{{x}}<br>%{{y:,.0f}}<extra></extra>", showlegend=False),
                      row=r, col=c)
        if len(g):
            fig.add_annotation(x=g.annee.iloc[-1], y=g.valeur.iloc[-1], text=f"<b>{compact(g.valeur.iloc[-1])}</b>",
                               showarrow=False, yshift=12, xanchor="right", font=dict(size=10, color=T.INK), row=r, col=c)
    _base(fig, hauteur, legende=False, marges=(8, 8, 28, 8))
    fig.update_xaxes(dtick=2, tickfont=dict(size=10), range=[2012.6, 2019.4])
    fig.update_yaxes(tickfont=dict(size=10), rangemode="tozero", nticks=4)
    for a in fig.layout.annotations[:n]:
        a.update(font=dict(size=11, color=T.INK))
    return fig


def sparkline(x, y, couleur: str = T.INK, hauteur: int = 90) -> go.Figure:
    fig = go.Figure(go.Scatter(x=list(x), y=list(y), mode="lines", line=dict(color=couleur, width=2),
                               fill="tozeroy", fillcolor="rgba(20,20,20,0.04)",
                               hovertemplate="%{x} : %{y:.1f} %<extra></extra>"))
    _base(fig, hauteur, legende=False, marges=(0, 0, 0, 0))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# ======================================================================================
# Barres horizontales
# ======================================================================================
def barres_h(labels, valeurs, couleurs=None, hauteur: int | None = None, texte=None, hover: list[str] | None = None,
             couleur: str = "#62625D", titre_x: str = "", max_px: float = 20) -> go.Figure:
    labels, valeurs = list(labels), list(valeurs)
    n = len(labels)
    hauteur = hauteur or max(160, 30 * n + 60)
    fig = go.Figure(go.Bar(
        y=labels, x=valeurs, orientation="h",
        marker_color=couleurs if couleurs is not None else couleur,
        text=texte, textposition="outside", cliponaxis=False, constraintext="none", textfont=dict(color=T.INK_2, size=11),
        hovertext=hover, hovertemplate="%{hovertext}<extra></extra>" if hover else "%{y} : %{x:,.1f}<extra></extra>"))
    droite = 16 + 7 * max((len(str(t)) for t in texte), default=4) if texte is not None else 56
    _base(fig, hauteur, legende=False, marges=(8, droite, 8, 8))
    fig.update_layout(bargap=_bargap(n, hauteur - 20, max_px))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=T.INK_2, size=12), automargin=True, ticksuffix="  ")
    fig.update_xaxes(showgrid=True, gridcolor=T.GRID, showticklabels=False, title_text=titre_x, rangemode="tozero")
    return fig


def barres_100(df: pd.DataFrame, cat: str, serie: str, valeur: str, couleurs: dict[str, str], ordre_series: list[str],
               hauteur: int = 220) -> go.Figure:
    tot = df.groupby(cat)[valeur].transform("sum")
    df = df.assign(part=100 * df[valeur] / tot)
    fig = go.Figure()
    for s in ordre_series:
        g = df[df[serie] == s]
        fig.add_trace(go.Bar(y=g[cat], x=g.part, name=s, orientation="h", marker_color=couleurs[s],
                             marker_line=dict(color=T.SURFACE, width=2),
                             text=[f"{nombre(p, 0)} %" if p >= 12 else "" for p in g.part], textposition="inside",
                             insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=11),
                             customdata=g[valeur],
                             hovertemplate=f"<b>%{{y}}</b> · {s}<br>%{{x:.1f}} % (%{{customdata:,.0f}})<extra></extra>"))
    _base(fig, hauteur, marges=(8, 8, 40, 8))
    fig.update_layout(barmode="stack", bargap=_bargap(df[cat].nunique(), hauteur - 60, 22), barcornerradius=0)
    fig.update_xaxes(ticksuffix=" %", range=[0, 100], showgrid=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, autorange="reversed", tickfont=dict(color=T.INK_2, size=12))
    return fig


def barres_ordinales(labels, valeurs, texte, hauteur: int = 260, couleurs=None, hover=None) -> go.Figure:
    labels = list(labels)
    couleurs = couleurs or T.RAMPE_CHAUDE[2:2 + len(labels)]
    fig = go.Figure(go.Bar(x=labels, y=list(valeurs), marker_color=couleurs, text=texte, textposition="outside", constraintext="none",
                           cliponaxis=False, textfont=dict(color=T.INK_2, size=11), hovertext=hover,
                           hovertemplate="%{hovertext}<extra></extra>" if hover else None))
    _base(fig, hauteur, legende=False, marges=(8, 8, 24, 8))
    fig.update_layout(bargap=_bargap(len(labels), 700, 48))
    fig.update_yaxes(showticklabels=False, showgrid=False, rangemode="tozero")
    return fig


# ======================================================================================
# Cartes
# ======================================================================================
def _zoom(lat: pd.Series, lon: pd.Series, hauteur: int) -> tuple[dict, float]:
    """Centre et zoom ajustés à l'emprise des points (référence : le Togo entier tient dans 520 px à 5,85)."""
    base = 5.85 + math.log2(hauteur / 520)
    if lat.empty:
        return CENTRE_TOGO, base
    la0, la1, lo0, lo1 = lat.min(), lat.max(), lon.min(), lon.max()
    centre = {"lat": (la0 + la1) / 2, "lon": (lo0 + lo1) / 2}
    etendue = max(la1 - la0, (lo1 - lo0) * 1.3, 0.03)
    return centre, float(min(12.5, max(base, base + math.log2(5.05 / etendue) - 0.25)))


def carte(hauteur: int = 640, lat: pd.Series | None = None, lon: pd.Series | None = None) -> go.Figure:
    fig = go.Figure()
    centre, zoom = _zoom(lat if lat is not None else pd.Series(dtype=float),
                         lon if lon is not None else pd.Series(dtype=float), hauteur)
    fig.update_layout(
        map=dict(style=STYLE_CARTE, center=centre, zoom=zoom),
        height=hauteur, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=T.FONT, size=12, color=T.INK_2),
        hoverlabel=dict(bgcolor=T.SURFACE, bordercolor=T.LINE, font=dict(family=T.FONT, size=12, color=T.INK)),
        legend=dict(orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.92)",
                    bordercolor=T.LINE, borderwidth=1, font=dict(size=12, color=T.INK), itemsizing="constant"),
        uirevision="carte",
    )
    return fig


def couche_choroplethe(fig: go.Figure, geojson: dict, df: pd.DataFrame, cle: str, valeur: str, titre: str,
                       echelle: list[str], hover: list[str], opacite: float = 0.72, fmt_barre: str = ",.0f") -> None:
    fig.add_trace(go.Choroplethmap(
        geojson=geojson, locations=df[cle], z=df[valeur], featureidkey=f"properties.{cle}",
        colorscale=[[i / (len(echelle) - 1), c] for i, c in enumerate(echelle)],
        marker=dict(opacity=opacite, line=dict(color="#FFFFFF", width=0.8)),
        colorbar=dict(title=dict(text=titre, side="top", font=dict(size=11, color=T.INK_2)), orientation="h",
                      thickness=9, len=0.42, x=0.98, xanchor="right", y=0.03, yanchor="bottom", outlinewidth=0,
                      tickformat=fmt_barre, nticks=4, tickfont=dict(size=10, color=T.INK_2), bgcolor="rgba(255,255,255,0.88)",
                      xpad=8, ypad=6),
        hovertext=hover, hovertemplate="%{hovertext}<extra></extra>", name=titre, showlegend=False))


def couche_points(fig: go.Figure, df: pd.DataFrame, nom: str, couleur: str, taille: float = 5, opacite: float = 0.75,
                  hover: list[str] | None = None, legende: bool = True) -> None:
    fig.add_trace(go.Scattermap(
        lat=df.lat, lon=df.lon, mode="markers", name=nom, showlegend=legende,
        marker=dict(size=taille, color=couleur, opacity=opacite),
        hovertext=hover, hovertemplate="%{hovertext}<extra></extra>" if hover is not None else f"{nom}<extra></extra>"))


def couche_densite(fig: go.Figure, df: pd.DataFrame, rayon: int = 9) -> None:
    fig.add_trace(go.Densitymap(
        lat=df.lat, lon=df.lon, radius=rayon, name="Densité d'agents MM", showscale=False,
        colorscale=[[0, "rgba(30,107,79,0)"], [0.2, "rgba(30,107,79,0.18)"], [0.55, "rgba(30,107,79,0.42)"], [1, "rgba(19,72,52,0.6)"]],
        hoverinfo="skip"))


# ======================================================================================
# Matrice de chaleur
# ======================================================================================
def matrice(rangs: pd.DataFrame, textes: pd.DataFrame, hover: pd.DataFrame, hauteur: int | None = None) -> go.Figure:
    n = len(rangs)
    hauteur = hauteur or max(260, 26 * n + 90)
    echelle = ["#F7F7F5", "#E7E7E3", "#D3D3CE", "#BCBCB6", "#A3A39C"]
    fig = go.Figure(go.Heatmap(
        z=rangs.values, x=list(rangs.columns), y=list(rangs.index), zmin=0, zmax=1,
        colorscale=[[i / 4, c] for i, c in enumerate(echelle)], xgap=2, ygap=2,
        text=textes.values, texttemplate="%{text}", textfont=dict(size=11, color=T.INK),
        customdata=hover.values, hovertemplate="%{customdata}<extra></extra>",
        colorbar=dict(title=dict(text="Rang centile<br>(1 = moins bien desservi)", font=dict(size=10)), thickness=10,
                      len=0.6, outlinewidth=0, tickvals=[0, 0.5, 1], ticktext=["0", "0,5", "1"], tickfont=dict(size=10))))
    _base(fig, hauteur, legende=False, marges=(8, 8, 8, 8))
    fig.update_xaxes(side="top", tickfont=dict(size=11, color=T.INK_2), showgrid=False, linecolor="rgba(0,0,0,0)")
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=T.INK))
    return fig
