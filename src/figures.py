"""Figures statiques du rapport (cartes et matrice) — mêmes calculs et même charte que le tableau de bord."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import config as C
from . import theme as T
from .formatage import entier, km, nombre, pct

plt.rcParams.update({
    "font.family": ["Calibri", "Segoe UI", "DejaVu Sans"],
    "font.size": 10, "axes.edgecolor": T.AXIS, "axes.labelcolor": T.INK_2,
    "xtick.color": T.MUTED, "ytick.color": T.MUTED, "savefig.dpi": 220, "figure.dpi": 110,
})


def _geo(nom: str) -> gpd.GeoDataFrame | None:
    p = C.PROCESSED_DIR / f"geo_{nom}.geojson"
    return gpd.read_file(p) if p.exists() else None


def _cadre(ax, pays) -> None:
    ax.set_axis_off()
    if pays is not None:
        pays.boundary.plot(ax=ax, color=T.INK_2, linewidth=0.8, zorder=5)
    ax.set_aspect("equal")


def _etiquettes(ax, points: list[tuple[float, float, str]], x_texte: float, ecart: float = 0.42) -> None:
    """Étiquettes alignées à droite de la carte, écartées verticalement pour ne jamais se chevaucher."""
    y_prec = None
    for x, y, txt in sorted(points, key=lambda p: -p[1]):
        yt = y if y_prec is None else min(y, y_prec - ecart)
        ax.annotate(txt, (x, y), xytext=(x_texte, yt), fontsize=8, color=T.INK, va="center", ha="left",
                    arrowprops=dict(arrowstyle="-", color=T.INK_2, lw=0.6, shrinkA=0, shrinkB=2), zorder=8)
        y_prec = yt


def carte_hab_etab(prefs: pd.DataFrame, finance: pd.DataFrame, chemin: Path) -> Path | None:
    g = _geo("prefectures")
    pays = _geo("pays")
    if g is None:
        return None
    d = g.merge(prefs, left_on="prefecture", right_on="territoire", how="left")
    b = d.total_bounds
    fig, ax = plt.subplots(figsize=(5.0, 7.2))
    cmap = LinearSegmentedColormap.from_list("chaud", T.RAMPE_CHAUDE[:7])
    avec = d[d.etablissements > 0]
    norm = Normalize(vmin=avec.hab_par_etab.min(), vmax=avec.hab_par_etab.max())
    avec.plot(ax=ax, column="hab_par_etab", cmap=cmap, norm=norm, edgecolor="white", linewidth=0.6, zorder=1)
    sans = d[d.etablissements == 0]
    if not sans.empty:
        sans.plot(ax=ax, color=T.CRITIQUE, edgecolor="white", linewidth=0.6, zorder=2)
    ax.scatter(finance.lon, finance.lat, s=2.2, color=T.INK, alpha=0.75, linewidths=0, zorder=6)
    _cadre(ax, pays)
    lab = pd.concat([sans, avec.nlargest(3, "hab_par_etab")])
    pts = []
    for _, r in lab.iterrows():
        c = r.geometry.representative_point()
        pts.append((c.x, c.y, f"{r.prefecture} : " + ("aucun établissement" if r.etablissements == 0 else f"{entier(r.hab_par_etab)} hab./étab.")))
    _etiquettes(ax, pts, b[2] + 0.12)
    ax.set_xlim(b[0] - 0.05, b[2] + 2.3)
    ax.set_ylim(b[1] - 0.1, b[3] + 0.1)
    cax = ax.inset_axes([0.55, 0.14, 0.42, 0.018])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7, length=0)
    cb.ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
    cb.ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: entier(v)))
    cb.set_label("Habitants par établissement", fontsize=7.5, color=T.INK_2)
    ax.legend(handles=[Patch(color=T.CRITIQUE, label="Aucun établissement observé"),
                       Line2D([], [], marker="o", ls="", color=T.INK, ms=3, label="Établissement (point GPS)")],
              loc="lower right", bbox_to_anchor=(1.0, 0.2), fontsize=7.5, frameon=False)
    fig.savefig(chemin, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return chemin


def carte_mm_seul(agents: pd.DataFrame, communes: pd.DataFrame, finance: pd.DataFrame, statut_mm_seul: str, chemin: Path) -> Path | None:
    g = _geo("prefectures")
    pays = _geo("pays")
    if g is None:
        return None
    a = agents.merge(communes[["territoire", "statut_couverture"]], left_on="unite_commune", right_on="territoire", how="left")
    seul = a[a.statut_couverture == statut_mm_seul]
    autres = a[a.statut_couverture != statut_mm_seul]
    b = g.total_bounds
    fig, ax = plt.subplots(figsize=(5.0, 7.2))
    g.plot(ax=ax, color="#F4F2EC", edgecolor="#D9D5C8", linewidth=0.5, zorder=1)
    ax.scatter(autres.lon, autres.lat, s=0.8, color="#9FB3A7", alpha=0.45, linewidths=0, zorder=2)
    ax.scatter(finance.lon, finance.lat, s=4, color=T.INK, marker="s", alpha=0.85, linewidths=0, zorder=3)
    ax.scatter(seul.lon, seul.lat, s=5, color=T.CRITIQUE, alpha=0.95, linewidths=0, zorder=4)
    _cadre(ax, pays)
    ax.set_xlim(b[0] - 0.05, b[2] + 2.3)
    ax.set_ylim(b[1] - 0.1, b[3] + 0.1)
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=T.CRITIQUE, ms=4,
               label="Agents MM, commune sans\nétablissement (" + entier(len(seul)) + ")"),
        Line2D([], [], marker="o", ls="", color="#9FB3A7", ms=4, label=f"Autres agents MM ({entier(len(autres))})"),
        Line2D([], [], marker="s", ls="", color=T.INK, ms=3.5,
               label="Établissements de\ndépôt/crédit (" + entier(len(finance)) + ")")],
        loc="lower right", bbox_to_anchor=(1.0, 0.12), fontsize=7.5, frameon=False, labelspacing=0.9)
    fig.savefig(chemin, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return chemin


def matrice(t: pd.DataFrame, n: int, chemin: Path) -> Path:
    m = t.sort_values("score", ascending=False).head(n)
    cols = ["hab_par_agent", "hab_par_etab", "dist_mediane_km", "part_eloignes_pct", "score"]
    noms = ["Hab. / agent MM", "Hab. / établissement", "Distance médiane", f"Agents > {C.SEUIL_ELOIGNEMENT_KM} km", "Rang moyen"]
    rangs = np.column_stack([m[f"rang_{c}"] if c != "score" else m.score for c in cols])
    fmt = {"hab_par_agent": entier, "hab_par_etab": entier, "dist_mediane_km": km, "part_eloignes_pct": lambda v: pct(v, 0),
           "score": lambda v: nombre(v, 2)}
    txt = [[("aucun" if (c == "hab_par_etab" and e == 0) else fmt[c](v)) for c in cols for v, e in [(r[c], r.etablissements)]]
           for _, r in m.iterrows()]
    cmap = LinearSegmentedColormap.from_list("chaud", ["#FBF1EA", "#F6DCCB", "#EEBC9E", "#E29A72", "#D3784C"])
    fig, ax = plt.subplots(figsize=(7.4, 0.36 * n + 0.8))
    ax.imshow(rangs, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(m)):
        for j in range(len(cols)):
            ax.text(j, i, txt[i][j], ha="center", va="center", fontsize=8.5, color=T.INK,
                    fontweight="bold" if j == len(cols) - 1 else "normal")
    ax.set_xticks(range(len(cols)), noms, fontsize=8.5, color=T.INK_2)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(m)), m.territoire, fontsize=9, color=T.INK)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(cols)), minor=True)
    ax.set_yticks(np.arange(-.5, len(m)), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    fig.savefig(chemin, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return chemin
