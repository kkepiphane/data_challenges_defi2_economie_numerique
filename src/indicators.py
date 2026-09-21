"""Calculs d'indicateurs : fonctions pures, partagées par le tableau de bord et le rapport.

Toutes les formules sont documentées dans FORMULES et reprises dans la fiche méthodologique.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config as C

FORMULES = {
    "hab_par_agent": "Population RGPH-5 2022 ÷ nombre d'agents mobile money recensés",
    "hab_par_etab": "Population RGPH-5 2022 ÷ nombre d'établissements financiers recensés (catégories et statuts sélectionnés)",
    "agents_10k": "Agents mobile money × 10 000 ÷ population",
    "etab_100k": "Établissements financiers × 100 000 ÷ population",
    "agents_par_etab": "Agents mobile money ÷ établissements financiers (même territoire)",
    "dist_mediane_km": "Médiane, sur les agents du territoire, de la distance à vol d'oiseau au plus proche établissement sélectionné",
    "part_eloignes_pct": f"Part des agents situés à plus de {C.SEUIL_ELOIGNEMENT_KM} km à vol d'oiseau de tout établissement sélectionné",
    "score": "Moyenne des rangs centiles (0 = mieux desservi, 1 = moins bien desservi) de 4 indicateurs, poids égaux : "
             "habitants par agent, habitants par établissement, distance médiane, part d'agents éloignés",
    "hhi": "Indice de Herfindahl-Hirschman = somme des carrés des parts de marché (en %) ; 10 000 = monopole",
    "variation_pp": "Valeur de l'année − valeur de l'année précédente (points de pourcentage)",
    "tcam": "Taux de croissance annuel moyen = (valeur finale ÷ valeur initiale)^(1 / nombre d'années) − 1",
}

LIBELLES = {
    "population": "Population (2022)",
    "agents": "Agents mobile money",
    "etablissements": "Établissements financiers",
    "hab_par_agent": "Habitants par agent MM",
    "hab_par_etab": "Habitants par établissement financier",
    "agents_10k": "Agents MM pour 10 000 hab.",
    "etab_100k": "Établissements pour 100 000 hab.",
    "agents_par_etab": "Agents MM par établissement financier",
    "dist_mediane_km": "Distance médiane agent → établissement (km)",
    "part_eloignes_pct": f"Agents à plus de {C.SEUIL_ELOIGNEMENT_KM} km d'un établissement (%)",
    "score": "Rang moyen de sous-desserte (0–1)",
}

STATUT_MM_ET_ETAB = "Agents MM et établissement(s)"
STATUT_MM_SEUL = "Agents MM, aucun établissement observé"
STATUT_ETAB_SEUL = "Établissement(s), aucun agent observé"
STATUT_AUCUN = "Aucun point observé"
STATUTS_COUVERTURE = [STATUT_MM_ET_ETAB, STATUT_MM_SEUL, STATUT_ETAB_SEUL, STATUT_AUCUN]

INDICATEURS_SOUS_DESSERTE = ["hab_par_agent", "hab_par_etab", "dist_mediane_km", "part_eloignes_pct"]


@dataclass(frozen=True)
class Filtres:
    periode: tuple[int, int] = C.PERIODE_DEFAUT
    regions: tuple[str, ...] = ()
    prefectures: tuple[str, ...] = ()
    communes: tuple[str, ...] = ()
    operateurs: tuple[str, ...] = tuple(C.OPERATEURS)
    inclure_op_nr: bool = True
    categories: tuple[str, ...] = tuple(C.FIN_CATEGORIES_DEFAULT)
    statuts: tuple[str, ...] = tuple(C.STATUT_DEFAULT)

    @property
    def geo_actif(self) -> bool:
        return bool(self.regions or self.prefectures or self.communes)

    def libelle_geo(self) -> str:
        for niveau, vals in [("Commune", self.communes), ("Préfecture", self.prefectures), ("Région", self.regions)]:
            if vals:
                return f"{niveau} : " + (", ".join(vals) if len(vals) <= 3 else f"{len(vals)} sélectionnées")
        return "Togo — ensemble du territoire"


# ======================================================================================
# Filtres
# ======================================================================================
def filtrer_agents(agents: pd.DataFrame, f: Filtres) -> pd.DataFrame:
    """Filtre opérateur : un agent est retenu s'il sert au moins un opérateur sélectionné."""
    garde = pd.Series(False, index=agents.index)
    if "Togocom" in f.operateurs:
        garde |= agents.sert_togocom
    if "Moov" in f.operateurs:
        garde |= agents.sert_moov
    if f.inclure_op_nr:
        garde |= agents.classe_operateur == C.OP_NR
    out = agents[garde].copy()
    out["dist_min_km"] = distance_min(out, f)
    return out


def distance_min(agents: pd.DataFrame, f: Filtres) -> pd.Series:
    cols = [C.dist_col(c, s) for c in f.categories for s in f.statuts if C.dist_col(c, s) in agents]
    if not cols:
        return pd.Series(np.nan, index=agents.index)
    return agents[cols].min(axis=1, skipna=True)


def filtrer_finance(fin: pd.DataFrame, f: Filtres) -> pd.DataFrame:
    return fin[fin.categorie.isin(f.categories) & fin.statut_groupe.isin(f.statuts)].copy()


def filtrer_geo(df: pd.DataFrame, f: Filtres) -> pd.DataFrame:
    m = pd.Series(True, index=df.index)
    if f.regions and "region" in df:
        m &= df.region.isin(f.regions)
    if f.prefectures and "prefecture" in df:
        m &= df.prefecture.isin(f.prefectures)
    if f.communes and "commune" in df:
        m &= df.commune.isin(f.communes)
    return df[m]


# ======================================================================================
# Tables territoriales
# ======================================================================================
def _cle_niveau(niveau: str) -> str:
    return {"region": "region", "prefecture": "prefecture", "commune": "unite_commune"}[niveau]


def table_territoriale(niveau: str, agents_f: pd.DataFrame, fin_f: pd.DataFrame, pop: dict[str, pd.DataFrame],
                       f: Filtres, seuil_km: float = C.SEUIL_ELOIGNEMENT_KM) -> pd.DataFrame:
    """Une ligne par territoire du niveau choisi. Les comptages portent sur l'ensemble des points
    (filtres opérateur/catégorie/statut appliqués) ; le filtre géographique sélectionne ensuite les lignes,
    ce qui garantit que numérateur et dénominateur couvrent exactement le même territoire."""
    k = _cle_niveau(niveau)
    base = {"region": pop["region"], "prefecture": pop["prefecture"], "commune": pop["commune"]}[niveau].copy()
    if niveau == "commune":
        base = base.rename(columns={"unite_commune": "territoire"})
    else:
        base = base.rename(columns={k: "territoire"})
        if niveau == "region":
            base["region"] = base["territoire"]
    base = base[[c for c in ["territoire", "region", "prefecture", "communes_bdd", "population"] if c in base]]

    ag = agents_f.groupby(k).agg(agents=("agent_id", "size"),
                                 dist_mediane_km=("dist_min_km", "median"),
                                 part_eloignes_pct=("dist_min_km", lambda d: 100 * (d > seuil_km).mean() if d.notna().any() else np.nan),
                                 agents_togocom=("sert_togocom", "sum"), agents_moov=("sert_moov", "sum"))
    et = fin_f.groupby(k).size().rename("etablissements")
    parcat = fin_f.pivot_table(index=k, columns="categorie", values="etab_id", aggfunc="size", fill_value=0)
    parcat.columns = [f"n_{c}" for c in parcat.columns]
    t = (base.merge(ag, left_on="territoire", right_index=True, how="left")
             .merge(et, left_on="territoire", right_index=True, how="left")
             .merge(parcat, left_on="territoire", right_index=True, how="left"))
    for c in ["agents", "etablissements", "agents_togocom", "agents_moov"] + list(parcat.columns):
        t[c] = t[c].fillna(0).astype(int)
    for cat in f.categories:
        if f"n_{cat}" not in t:
            t[f"n_{cat}"] = 0
    t["hab_par_agent"] = np.where(t.agents > 0, t.population / t.agents.replace(0, np.nan), np.nan)
    t["hab_par_etab"] = np.where(t.etablissements > 0, t.population / t.etablissements.replace(0, np.nan), np.nan)
    t["agents_10k"] = 1e4 * t.agents / t.population
    t["etab_100k"] = 1e5 * t.etablissements / t.population
    t["agents_par_etab"] = np.where(t.etablissements > 0, t.agents / t.etablissements.replace(0, np.nan), np.nan)
    t["statut_couverture"] = np.select(
        [(t.agents > 0) & (t.etablissements > 0), t.agents > 0, t.etablissements > 0],
        [STATUT_MM_ET_ETAB, STATUT_MM_SEUL, STATUT_ETAB_SEUL], STATUT_AUCUN)
    t = ajouter_score(t)
    return filtrer_lignes_territoire(t, niveau, f, pop)


def perimetre(f: Filtres, pop: dict[str, pd.DataFrame]) -> dict[str, set[str] | None]:
    """Territoires couverts par la sélection la plus fine (commune > préfecture > région).
    None = pas de restriction à ce niveau."""
    pc = pop["commune"]
    if f.communes:
        u = pc[pc.communes_bdd.apply(lambda s: any(c in f.communes for c in s.split("|")))]
    elif f.prefectures:
        u = pc[pc.prefecture.isin(f.prefectures)]
    elif f.regions:
        u = pc[pc.region.isin(f.regions)]
    else:
        return {"region": None, "prefecture": None, "commune": None}
    return {"region": set(u.region), "prefecture": set(u.prefecture), "commune": set(u.unite_commune)}


def filtrer_lignes_territoire(t: pd.DataFrame, niveau: str, f: Filtres, pop: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sel = perimetre(f, pop)[niveau]
    return (t if sel is None else t[t.territoire.isin(sel)]).reset_index(drop=True)


def ajouter_score(t: pd.DataFrame) -> pd.DataFrame:
    """Rangs centiles orientés « plus haut = moins bien desservi ». Un territoire sans aucun point
    du type considéré est classé au rang le plus défavorable (valeur infinie avant classement)."""
    t = t.copy()
    rangs = []
    for c in INDICATEURS_SOUS_DESSERTE:
        v = t[c].copy()
        if c == "hab_par_agent":
            v = v.where(t.agents > 0, np.inf)
        elif c == "hab_par_etab":
            v = v.where(t.etablissements > 0, np.inf)
        if v.notna().sum() < 2:
            continue
        r = v.rank(pct=True, method="average")
        t[f"rang_{c}"] = r
        rangs.append(r)
    t["score"] = pd.concat(rangs, axis=1).mean(axis=1, skipna=True) if rangs else np.nan
    return t


def presence_canton(agents_f: pd.DataFrame, fin_f: pd.DataFrame, f: Filtres) -> pd.DataFrame:
    cles = ["region", "prefecture", "commune", "canton"]
    a = agents_f.groupby(cles).size().rename("agents")
    e = fin_f.groupby(cles).size().rename("etablissements")
    t = pd.concat([a, e], axis=1).fillna(0).astype(int).reset_index()
    t["statut_couverture"] = np.select(
        [(t.agents > 0) & (t.etablissements > 0), t.agents > 0], [STATUT_MM_ET_ETAB, STATUT_MM_SEUL], STATUT_ETAB_SEUL)
    return filtrer_geo(t, f)


def bandes_distance(agents_f: pd.DataFrame) -> pd.DataFrame:
    d = agents_f.dist_min_km.dropna()
    if d.empty:
        return pd.DataFrame(columns=["bande", "agents", "part_pct"])
    b = pd.cut(d, C.DIST_BANDES, labels=C.DIST_LABELS, right=False).value_counts().reindex(C.DIST_LABELS).fillna(0)
    return pd.DataFrame({"bande": C.DIST_LABELS, "agents": b.values.astype(int), "part_pct": 100 * b.values / len(d)})


def synthese_nationale(agents_f: pd.DataFrame, fin_f: pd.DataFrame, pop_total: int) -> dict:
    return {
        "population": pop_total,
        "agents": len(agents_f),
        "etablissements": len(fin_f),
        "hab_par_agent": pop_total / len(agents_f) if len(agents_f) else np.nan,
        "hab_par_etab": pop_total / len(fin_f) if len(fin_f) else np.nan,
        "agents_par_etab": len(agents_f) / len(fin_f) if len(fin_f) else np.nan,
        "dist_mediane_km": agents_f.dist_min_km.median(),
        "part_eloignes_pct": 100 * (agents_f.dist_min_km > C.SEUIL_ELOIGNEMENT_KM).mean() if len(agents_f) else np.nan,
    }


# ======================================================================================
# Séries temporelles
# ======================================================================================
def phases_internet(s: pd.DataFrame, seuil_pp: float = 0.25, tolerance_pp: float = 0.1) -> pd.DataFrame:
    """Qualifie chaque variation annuelle (règles transparentes, seuils modifiables) :
    recul : variation < −seuil ; stagnation : |variation| ≤ seuil ;
    accélération : variation > variation précédente + tolérance ;
    rythme constant : écart à la variation précédente ≤ tolérance ; sinon progression ralentie."""
    d = s.dropna(subset=["valeur_pct"]).sort_values("annee").copy()
    d["variation_pp"] = d.valeur_pct.diff()
    d["croissance_pct"] = 100 * d.valeur_pct.pct_change().replace([np.inf, -np.inf], np.nan)
    v, prec = d.variation_pp, d.variation_pp.shift(1)
    d["phase"] = np.select(
        [v.isna(), v < -seuil_pp, v.abs() <= seuil_pp, prec.isna(), v > prec + tolerance_pp, (v - prec).abs() <= tolerance_pp],
        ["—", "Recul", "Stagnation", "—", "Accélération", "Rythme constant"], "Progression ralentie")
    return d.reset_index(drop=True)


def episodes(d: pd.DataFrame) -> pd.DataFrame:
    """Regroupe les années consécutives de même phase."""
    d = d[d.phase != "—"]
    if d.empty:
        return pd.DataFrame(columns=["phase", "debut", "fin", "annees", "gain_pp"])
    grp = (d.phase != d.phase.shift()).cumsum()
    return (d.groupby(grp).agg(phase=("phase", "first"), debut=("annee", "min"), fin=("annee", "max"),
                               annees=("annee", "size"), gain_pp=("variation_pp", "sum")).reset_index(drop=True))


def tcam(v0: float, v1: float, n: int) -> float:
    if not n or v0 is None or v0 <= 0 or pd.isna(v0) or pd.isna(v1):
        return np.nan
    return 100 * ((v1 / v0) ** (1 / n) - 1)


def serie(tel: pd.DataFrame, indicateur_source: str) -> pd.Series:
    d = tel[tel.indicateur_source == indicateur_source]
    return d.set_index("annee").valeur.sort_index()


def hhi_parts(tel: pd.DataFrame) -> pd.DataFrame:
    p = tel[tel.famille == "Marché — parts"].pivot_table(index="annee", columns="groupe", values="valeur")
    p["hhi"] = (p ** 2).sum(axis=1)
    p["ecart_pp"] = (p.get("Togocom") - p.get("Moov")).abs()
    return p.reset_index()
