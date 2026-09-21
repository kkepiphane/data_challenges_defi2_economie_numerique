"""Pipeline reproductible : sources brutes (lecture seule) → tables nettoyées dans data_processed/.

Usage : python -m src.pipeline

Aucune valeur n'est imputée ni estimée. Chaque transformation est tracée dans
data_processed/controles_qualite.csv (contrôle, résultat, détail).
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from . import config as C
from .normalisation import cle, numero_final
from .series_meta import COLONNES, META

NIVEAUX_POP = ["pays", "region_rgph", "prefecture", "commune", "canton_ou_quartier"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
JOURS_COURTS = dict(zip(JOURS, ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))
R_TERRE_KM = 6371.0088


class Controles:
    def __init__(self) -> None:
        self.lignes: list[dict] = []

    def ajouter(self, domaine: str, controle: str, ok: bool, detail: str = "") -> None:
        self.lignes.append({"domaine": domaine, "controle": controle,
                            "resultat": "OK" if ok else "ÉCART", "detail": detail})
        print(f"[{'OK' if ok else 'ÉCART':5}] {domaine} — {controle} {('· ' + detail) if detail else ''}")

    def table(self) -> pd.DataFrame:
        return pd.DataFrame(self.lignes)


def _fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def _lire(nom: str, **kw) -> pd.DataFrame:
    return pd.read_csv(C.DATA_DIR / nom, encoding="utf-8", **kw)


def _coords(wkt: pd.Series) -> pd.DataFrame:
    xy = wkt.str.extract(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)").astype(float)
    xy.columns = ["lon", "lat"]
    return xy


# ======================================================================================
# Population RGPH-5
# ======================================================================================
def construire_population(ctrl: Controles, bdd: pd.DataFrame) -> dict[str, pd.DataFrame]:
    raw = _lire(C.SRC_POPULATION)
    raw.columns = ["indicateur", "zone", "sexe", "unite", "annee", "valeur"]
    ctrl.ajouter("Population", "Indicateur, sexe, unité et année uniques",
                 raw[["indicateur", "sexe", "unite", "annee"]].nunique().max() == 1,
                 f"{raw.indicateur.iloc[0]} · sexe={raw.sexe.iloc[0]} · {raw.annee.iloc[0]}")
    ctrl.ajouter("Population", "Aucune valeur manquante", raw.valeur.notna().all(), f"{len(raw)} lignes")

    # Reconstruction de l'arbre : chaque nœud non terminal est suivi de ses enfants,
    # dont la somme doit égaler exactement sa population.
    noeuds, pile = [], []
    for i, (zone, val) in enumerate(zip(raw.zone, raw.valeur.astype(int))):
        prof = len(pile)
        if i > 0 and prof == 0:
            raise ValueError(f"Ligne {i} ({zone}) hors hiérarchie : la somme des niveaux est incohérente")
        n = {"ligne_source": i + 2, "niveau": NIVEAUX_POP[prof], "libelle_source": zone,
             "population": val, "parent": pile[-1]["ligne_source"] if pile else None, "_reste": val, "_enfants": []}
        if pile:
            pile[-1]["_reste"] -= val
            pile[-1]["_enfants"].append(n)
        noeuds.append(n)
        if prof < 4:
            pile.append(n)
        while pile and pile[-1]["_reste"] == 0:
            pile.pop()
    ctrl.ajouter("Population", "Hiérarchie reconstruite sans reste (somme des enfants = parent à chaque nœud)",
                 not pile and all(n["_reste"] == 0 for n in noeuds if n["_enfants"]),
                 f"{len(noeuds)} nœuds")
    racine = noeuds[0]
    ctrl.ajouter("Population", "Total national = 8 095 498 (RGPH-5, identique au livret INSEED du Défi 1)",
                 racine["population"] == 8_095_498, _fmt(racine["population"]))

    prefs_bdd = {cle(p): p for p in bdd.prefecture_nom_bdd.unique()}
    communes_bdd = set(bdd.commune_nom_bdd.unique())
    pref_region_bdd = bdd.drop_duplicates("prefecture_nom_bdd").set_index("prefecture_nom_bdd").region_nom_bdd

    lignes_pref, lignes_unite, lignes_hier = [], [], []
    for reg in racine["_enfants"]:
        region_bdd = C.RGPH_REGION_TO_BDD[reg["libelle_source"]]
        reg.update(region_bdd=region_bdd)
        for pref in reg["_enfants"]:
            k = cle(pref["libelle_source"])
            pref_bdd = prefs_bdd.get(C.RGPH_PREFECTURE_ALIASES.get(k, k))
            if pref_bdd is None:
                raise ValueError(f"Préfecture non appariée : {pref['libelle_source']}")
            pref.update(region_bdd=region_bdd, prefecture_bdd=pref_bdd,
                        correction="" if cle(pref_bdd) == k else f"libellé source « {pref['libelle_source']} » → {pref_bdd}")
            lignes_pref.append({"region": region_bdd, "prefecture": pref_bdd, "population": pref["population"],
                                "libelle_source": pref["libelle_source"], "region_rgph": reg["libelle_source"]})
            rang = 0
            for com in pref["_enfants"]:
                lib = com["libelle_source"]
                nums = [int(x) for x in re.findall(r"\d+", lib)]
                if "+" in lib:
                    communes = [f"{pref_bdd} {n}" for n in nums]
                    rang = max(nums)
                    unite = " + ".join(communes)
                    correction = f"unité fusionnée dans la source (« {lib} ») : population commune non séparable"
                else:
                    rang += 1
                    communes = [f"{pref_bdd} {rang}"]
                    unite = communes[0]
                    n_lib = numero_final(lib)
                    if n_lib != rang:
                        correction = f"libellé source « {lib} » en position {rang} → {unite} (somme des cantons vérifiée)"
                    elif cle(lib) != cle(unite):
                        correction = f"libellé source « {lib} » normalisé en {unite}"
                    else:
                        correction = ""
                manquantes = [c for c in communes if c not in communes_bdd]
                if manquantes:
                    raise ValueError(f"Commune(s) absente(s) de la base PRISE : {manquantes}")
                com.update(region_bdd=region_bdd, prefecture_bdd=pref_bdd, commune_bdd=unite, correction=correction)
                lignes_unite.append({"region": region_bdd, "prefecture": pref_bdd, "unite_commune": unite,
                                     "communes_bdd": "|".join(communes), "population": com["population"],
                                     "libelle_source": lib, "correction": correction})
                for cant in com["_enfants"]:
                    cant.update(region_bdd=region_bdd, prefecture_bdd=pref_bdd, commune_bdd=unite)

    for n in noeuds:
        lignes_hier.append({k: n.get(k, "") for k in ["ligne_source", "niveau", "libelle_source", "population", "parent",
                                                        "region_bdd", "prefecture_bdd", "commune_bdd", "correction"]})
    hier = pd.DataFrame(lignes_hier)
    pop_pref = pd.DataFrame(lignes_pref)
    pop_unite = pd.DataFrame(lignes_unite)

    ctrl.ajouter("Population", "39 préfectures appariées aux noms de la base PRISE",
                 pop_pref.prefecture.nunique() == 39 and set(pop_pref.prefecture) == set(bdd.prefecture_nom_bdd),
                 f"{pop_pref.prefecture.nunique()}/39")
    region_ok = all(pref_region_bdd[p] == r for p, r in zip(pop_pref.prefecture, pop_pref.region))
    ctrl.ajouter("Population", "Rattachement préfecture → région identique RGPH-5 / PRISE", region_ok,
                 "Grand Lomé (DAGL) rattaché à Maritime comme dans la base PRISE")
    communes_couvertes = {c for s in pop_unite.communes_bdd for c in s.split("|")}
    ctrl.ajouter("Population", "117 communes PRISE couvertes par 116 unités de population",
                 communes_couvertes == communes_bdd and len(pop_unite) == 116,
                 f"{len(communes_couvertes)} communes · {len(pop_unite)} unités (Danyi 1 + Danyi 2 fusionnées)")
    ctrl.ajouter("Population", "Somme préfectorale = somme communale = total national",
                 pop_pref.population.sum() == pop_unite.population.sum() == racine["population"],
                 _fmt(pop_pref.population.sum()))
    for _, r in pop_unite[pop_unite.correction != ""].iterrows():
        ctrl.ajouter("Population", f"Correction de libellé — {r.unite_commune}", True, r.correction)

    pop_region = (pop_pref.groupby("region", as_index=False)
                  .agg(population=("population", "sum"), regions_rgph=("region_rgph", lambda s: " + ".join(sorted(set(s))))))
    commune_vers_unite = pd.DataFrame([{"commune": c, "unite_commune": u}
                                       for u, s in zip(pop_unite.unite_commune, pop_unite.communes_bdd)
                                       for c in s.split("|")])
    return {"population_hierarchie": hier, "population_region": pop_region,
            "population_prefecture": pop_pref, "population_commune": pop_unite,
            "commune_vers_unite": commune_vers_unite}


# ======================================================================================
# Agents mobile money et établissements financiers
# ======================================================================================
def construire_agents(ctrl: Controles, ag: pd.DataFrame, cvu: pd.DataFrame) -> pd.DataFrame:
    ctrl.ajouter("Agents MM", "Aucune valeur manquante", ag.notna().all().all(), f"{len(ag)} lignes × {ag.shape[1]} colonnes")
    ctrl.ajouter("Agents MM", "Identifiants FID uniques", ag.FID.is_unique, "")
    ctrl.ajouter("Agents MM", "Aucune géométrie dupliquée", ag.geometry.is_unique, "")
    xy = _coords(ag.geometry)
    ops = ag.operateur.str.split(",").apply(lambda l: {s.strip() for s in l})
    out = pd.DataFrame({
        "agent_id": ag.FID,
        "region": ag.region_nom_bdd, "prefecture": ag.prefecture_nom_bdd,
        "commune": ag.commune_nom_bdd, "canton": ag.canton_nom_bdd,
        "operateur_source": ag.operateur,
        "sert_togocom": ops.apply(lambda s: "Togocom" in s),
        "sert_moov": ops.apply(lambda s: "Moov" in s),
        "lon": xy.lon, "lat": xy.lat,
    })
    out["classe_operateur"] = np.select(
        [out.sert_moov & out.sert_togocom, out.sert_togocom, out.sert_moov],
        ["Moov + Togocom", "Togocom seul", "Moov seul"], C.OP_NR)
    reconnus = ops.apply(lambda s: s <= {"Moov", "Togocom", "Nsp"}).all()
    ctrl.ajouter("Agents MM", "Valeurs d'opérateur reconnues (Moov, Togocom, Nsp)", reconnus,
                 " · ".join(f"{k} : {_fmt(v)}" for k, v in ag.operateur.value_counts().items()))
    out = out.merge(cvu, on="commune", how="left")
    ctrl.ajouter("Agents MM", "Tous les agents rattachés à une unité de population communale",
                 out.unite_commune.notna().all(), f"{out.unite_commune.notna().sum()}/{len(out)}")
    return out


def _jours(val: str) -> tuple[str, int, bool, bool, bool]:
    if not str(val).startswith("{"):
        return ("Non renseigné", 0, False, False, False)
    js = {t.strip().lower() for t in str(val).strip("{}").split(",")}
    js = [j for j in JOURS if j in js]
    return ("–".join(JOURS_COURTS[j] for j in js), len(js), "samedi" in js, "dimanche" in js, True)


def construire_finance(ctrl: Controles, fi: pd.DataFrame, cvu: pd.DataFrame) -> pd.DataFrame:
    ctrl.ajouter("Établissements", "Aucune valeur manquante", fi.notna().all().all(), f"{len(fi)} lignes × {fi.shape[1]} colonnes")
    ctrl.ajouter("Établissements", "Identifiants FID uniques", fi.FID.is_unique, "")
    ctrl.ajouter("Établissements", "Aucune géométrie dupliquée", fi.geometry.is_unique, "")
    inconnues = set(fi.activite_categorie) - set(C.FIN_CATEGORY_MAP)
    ctrl.ajouter("Établissements", "Catégories reconnues ; « Micro-Finace » fusionnée avec « Micro-Finance »",
                 not inconnues, " · ".join(f"{k} : {v}" for k, v in fi.activite_categorie.value_counts().items()))
    fi = fi.assign(activite_statut=fi.activite_statut.str.strip())
    statuts_inconnus = set(fi.activite_statut) - set(C.STATUT_MAP)
    ctrl.ajouter("Établissements", "Statuts d'activité regroupés en 3 classes", not statuts_inconnus,
                 " · ".join(f"{k} : {v}" for k, v in fi.activite_statut.value_counts().items()))
    xy = _coords(fi.geometry)
    jours = fi.etab_jour.apply(_jours)
    out = pd.DataFrame({
        "etab_id": fi.FID,
        "nom": fi.etab_nom.str.strip(),
        "localite": fi.nom_localite.str.strip(),
        "region": fi.region_nom_bdd, "prefecture": fi.prefecture_nom_bdd,
        "commune": fi.commune_nom_bdd, "canton": fi.canton_nom_bdd,
        "categorie": fi.activite_categorie.map(C.FIN_CATEGORY_MAP),
        "categorie_source": fi.activite_categorie,
        "statut_source": fi.activite_statut,
        "statut_groupe": fi.activite_statut.map(C.STATUT_MAP),
        "jours_ouverture": [j[0] for j in jours],
        "nb_jours_ouverture": [j[1] for j in jours],
        "ouvert_samedi": [j[2] for j in jours],
        "ouvert_dimanche": [j[3] for j in jours],
        "jours_renseignes": [j[4] for j in jours],
        "lon": xy.lon, "lat": xy.lat,
    })
    ctrl.ajouter("Établissements", "Jours d'ouverture exploitables", True,
                 f"{sum(j[4] for j in jours)}/{len(out)} renseignés (casse harmonisée)")
    dup_noms = out[out.duplicated(["nom", "commune"], keep=False)]
    ctrl.ajouter("Établissements", "Homonymes dans une même commune (signalés, conservés : coordonnées distinctes)",
                 True, f"{len(dup_noms)} enregistrements")
    out = out.merge(cvu, on="commune", how="left")
    ctrl.ajouter("Établissements", "Tous les établissements rattachés à une unité de population communale",
                 out.unite_commune.notna().all(), f"{out.unite_commune.notna().sum()}/{len(out)}")
    return out


def calculer_distances(ctrl: Controles, agents: pd.DataFrame, fin: pd.DataFrame) -> pd.DataFrame:
    """Distance à vol d'oiseau (grand cercle) de chaque agent au plus proche établissement,
    pour chaque combinaison catégorie × statut. L'application prend le minimum sur la sélection."""
    from sklearn.neighbors import BallTree

    pts = np.radians(agents[["lat", "lon"]].to_numpy())
    for cat in C.FIN_CATEGORIES:
        for st in C.STATUT_GROUPES:
            sub = fin[(fin.categorie == cat) & (fin.statut_groupe == st)]
            col = C.dist_col(cat, st)
            if sub.empty:
                agents[col] = np.nan
                continue
            arbre = BallTree(np.radians(sub[["lat", "lon"]].to_numpy()), metric="haversine")
            d, _ = arbre.query(pts, k=1)
            agents[col] = np.round(d[:, 0] * R_TERRE_KM, 3)
    ctrl.ajouter("Distances", "Distance au plus proche établissement calculée (12 combinaisons catégorie × statut)",
                 True, "BallTree haversine, rayon terrestre 6 371 km ; établissements hors Togo non couverts par les données")
    return agents


# ======================================================================================
# Géométries (Défi 1) et cohérence spatiale
# ======================================================================================
def construire_geo(ctrl: Controles, agents: pd.DataFrame, fin: pd.DataFrame) -> dict:
    import geopandas as gpd

    chemin = next((p for p in C.DEFI1_GEOMETRY_CANDIDATES if p.exists()), None)
    if chemin is None:
        ctrl.ajouter("Géométrie", "Contours préfectoraux du Défi 1 disponibles", False,
                     "Cartes choroplèthes indisponibles ; les points restent cartographiables")
        agents["prefecture_geom"] = None
        fin["prefecture_geom"] = None
        return {}
    pref = gpd.read_file(chemin)[["pcode", "prefecture", "region", "geometry"]].to_crs(4326)
    ctrl.ajouter("Géométrie", "Contours préfectoraux (COD-AB OCHA, réconciliés au Défi 1) : 39 unités, noms PRISE",
                 len(pref) == 39 and set(pref.prefecture) == set(agents.prefecture), f"{chemin.name}")
    laea = "+proj=laea +lat_0=8.6 +lon_0=0.9 +datum=WGS84 +units=m"
    pref["superficie_km2"] = (pref.to_crs(laea).area / 1e6).round(1)

    for nom, df in [("Agents MM", agents), ("Établissements", fin)]:
        g = gpd.GeoDataFrame(df[["lon", "lat"]], geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
        j = gpd.sjoin(g, pref[["prefecture", "geometry"]], how="left", predicate="within")
        j = j[~j.index.duplicated()]
        df["prefecture_geom"] = j.prefecture.values
        dedans = df.prefecture_geom.notna()
        concord = (df.prefecture_geom == df.prefecture) & dedans
        df["coherence_geo"] = np.where(~dedans, "Hors contour (bordure)", np.where(concord, "Concordant", "Préfecture voisine"))
        ctrl.ajouter("Géométrie", f"{nom} : points situés dans un contour préfectoral", dedans.mean() > 0.99,
                     f"{dedans.sum()}/{len(df)} ({dedans.mean():.2%}) ; les autres sont en limite de frontière")
        ctrl.ajouter("Géométrie", f"{nom} : préfecture géométrique = préfecture déclarée", concord.sum() / dedans.sum() > 0.95,
                     f"{concord.sum()}/{dedans.sum()} ({concord.sum() / dedans.sum():.2%}) ; l'attribut déclaré fait foi pour les agrégations")

    simp = pref.copy()
    simp["geometry"] = simp.geometry.simplify(0.0025, preserve_topology=True)
    regions = pref.dissolve(by="region", as_index=False)[["region", "geometry"]]
    regions["superficie_km2"] = (regions.to_crs(laea).area / 1e6).round(1)
    regions["geometry"] = regions.geometry.simplify(0.0025, preserve_topology=True)
    pays = pref.dissolve()[["geometry"]]
    pays["geometry"] = pays.geometry.simplify(0.0025, preserve_topology=True)
    ctrl.ajouter("Géométrie", "Superficie totale (projection équivalente LAEA)", True,
                 f"{_fmt(pref.superficie_km2.sum())} km²")
    return {"prefectures": simp, "regions": regions, "pays": pays}


# ======================================================================================
# Séries temporelles
# ======================================================================================
def construire_series(ctrl: Controles) -> dict[str, pd.DataFrame]:
    bm = _lire(C.SRC_INTERNET_BM)
    ctrl.ajouter("Internet (BM)", "Pays et indicateur uniques",
                 bm.countryiso3code.nunique() == 1 and bm.indicator.nunique() == 1,
                 f"{bm.country.iloc[0]} · {bm.indicator.iloc[0]}")
    s = pd.DataFrame({"annee": bm.date.astype(int), "valeur_pct": bm.value,
                      "indicateur": bm.indicator.iloc[0], "source": C.SOURCES[C.SRC_INTERNET_BM]["producteur"]})
    s = s.sort_values("annee").reset_index(drop=True)
    s["observation"] = np.where(s.valeur_pct.isna(), "Valeur manquante dans la source", "")
    manquantes = s.loc[s.valeur_pct.isna(), "annee"].tolist()
    ctrl.ajouter("Internet (BM)", "Valeurs comprises entre 0 et 100 %", s.valeur_pct.dropna().between(0, 100).all(),
                 f"dernière année renseignée : {int(s.dropna().annee.max())} ({s.dropna().valeur_pct.iloc[-1]:.1f} %)")
    ctrl.ajouter("Internet (BM)", "Années sans valeur (non imputées)", True, ", ".join(map(str, manquantes)))

    frames = []
    for fichier in [C.SRC_TELECOM_INTERNET, C.SRC_TELECOM_MARCHE]:
        d = _lire(fichier)
        d.columns = ["indicateur_source", "unite_source", "annee", "valeur"]
        frames.append(d)
    t = pd.concat(frames, ignore_index=True)
    non_mappes = set(t.indicateur_source) - set(META)
    ctrl.ajouter("Télécoms", "Tous les indicateurs sources documentés", not non_mappes, f"{t.indicateur_source.nunique()} indicateurs")
    meta = pd.DataFrame.from_dict(META, orient="index", columns=COLONNES).rename_axis("indicateur_source").reset_index()
    t = t.merge(meta, on="indicateur_source", how="left")
    t["annee"] = t.annee.astype(int)
    ctrl.ajouter("Télécoms", "Aucun doublon indicateur × année", not t.duplicated(["indicateur_source", "annee"]).any(), "")
    ctrl.ajouter("Télécoms", "Aucune valeur manquante", t.valeur.notna().all(), f"{len(t)} observations, {t.annee.min()}–{t.annee.max()}")

    piv = t.pivot_table(index="annee", columns="indicateur_source", values="valeur")

    def egal(a, b, tol=0.0):
        m = pd.concat([a, b], axis=1).dropna()
        return bool(((m.iloc[:, 0] - m.iloc[:, 1]).abs() <= tol).all()), len(m)

    ok, n = egal(piv["Part de marché Togo Cellulaire (en abonnées) en %"] + piv["Part de marché Atlantique Telecom Togo (en abonnées)"],
                 pd.Series(100.0, index=piv.index), 0.011)
    ctrl.ajouter("Télécoms", "Parts de marché Togocom + Moov = 100 %", ok, f"{n} années")
    ok, n = egal(piv["Le nombre total d'abonnées mobiles GSM"] + piv["Le nombre total d'abonnés fixe"], piv["Le nombre total d'abonnés fixe et mobile"])
    ctrl.ajouter("Télécoms", "Abonnés fixe + mobile = abonnés GSM + abonnés fixe", ok, f"{n} années")
    ok, n = egal(piv["T Togo Cellulaire"] + piv["T Atlantique Telecom"], piv["T abonnés Internet mobiles (Toutes technologies)"])
    ctrl.ajouter("Télécoms", "Internet mobile total = Togocom + Moov", ok, f"{n} années")
    hd = (piv["Nombre de clients 3G Togo Cellulaire"] + piv["Nombre de clients 3G Atlantique Telecom"]
          + piv["Nombre de clients 4G Togo Cellulaire"] + piv["Nombre de clients 4G Atlantique Telecom"].fillna(0))
    ok, n = egal(hd, piv["T abonnés Internet mobiles (Haut débit)"])
    ctrl.ajouter("Télécoms", "Internet mobile haut débit = 3G + 4G des deux opérateurs", ok,
                 f"{n} années ; 4G Moov absente de la source en 2018–2019 (égalité vérifiée sans elle, aucune valeur imputée)")
    tc = piv["Abonnés GPRS /EDGE Togo Cellulaire"] + piv["Nombre de clients 3G Togo Cellulaire"] + piv["Nombre de clients 4G Togo Cellulaire"]
    ok, n = egal(tc, piv["T Togo Cellulaire"])
    ctrl.ajouter("Télécoms", "Total Togocom = 2G + 3G + 4G", ok, f"{n} années")
    at = piv["Abonnés GPRS/EDGE Atlantique Telecom"] + piv["Nombre de clients 3G Atlantique Telecom"] + piv["Nombre de clients 4G Atlantique Telecom"].fillna(0)
    ok, n = egal(at, piv["T Atlantique Telecom"])
    ctrl.ajouter("Télécoms", "Total Moov = 2G + 3G (+ 4G si renseignée)", ok, f"{n} années")
    arpu, ca = piv["ARPU segment mobile GSM"], piv["Chiffres d'Affaires"]
    ctrl.ajouter("Télécoms", "ARPU cohérent avec l'unité déclarée (FCFA)", bool((arpu < ca).all()),
                 f"ARPU 2019 = {arpu[2019]:.3g} FCFA > CA 2019 = {ca[2019]:.3g} FCFA → série exclue des graphiques")
    ctrl.ajouter("Télécoms", "Unité des taux de pénétration Internet", False,
                 "unité source « Nombre » alors que le libellé indique (%) : valeurs conservées, unité affichée %")
    return {"series_internet_bm": s, "series_telecom": t}


# ======================================================================================
def main() -> None:
    C.PROCESSED_DIR.mkdir(exist_ok=True)
    ctrl = Controles()
    ag = _lire(C.SRC_AGENTS)
    fi = _lire(C.SRC_FINANCE)
    bdd = pd.concat([d[["region_nom_bdd", "prefecture_nom_bdd", "commune_nom_bdd", "canton_nom_bdd"]] for d in (ag, fi)])

    for nom, d in [("Agents MM", ag), ("Établissements", fi)]:
        h = d[["region_nom_bdd", "prefecture_nom_bdd", "commune_nom_bdd"]].drop_duplicates()
        ok = h.commune_nom_bdd.is_unique and h.drop_duplicates(["region_nom_bdd", "prefecture_nom_bdd"]).prefecture_nom_bdd.is_unique
        ctrl.ajouter(nom, "Hiérarchie région → préfecture → commune sans conflit", ok,
                     f"{d.region_nom_bdd.nunique()} régions · {d.prefecture_nom_bdd.nunique()} préfectures · "
                     f"{d.commune_nom_bdd.nunique()} communes · {d.canton_nom_bdd.nunique()} cantons")

    pop = construire_population(ctrl, bdd)
    agents = construire_agents(ctrl, ag, pop["commune_vers_unite"])
    fin = construire_finance(ctrl, fi, pop["commune_vers_unite"])
    geo = construire_geo(ctrl, agents, fin)
    agents = calculer_distances(ctrl, agents, fin)
    series = construire_series(ctrl)

    tables = {**pop, **series, "agents_mobile_money": agents, "etablissements_financiers": fin}
    for nom, df in tables.items():
        df.to_csv(C.PROCESSED_DIR / f"{nom}.csv", index=False, encoding="utf-8")
    for nom, g in geo.items():
        chemin = C.PROCESSED_DIR / f"geo_{nom}.geojson"
        chemin.unlink(missing_ok=True)
        g.to_file(chemin, driver="GeoJSON", COORDINATE_PRECISION=5)
    ctrl.table().to_csv(C.PROCESSED_DIR / "controles_qualite.csv", index=False, encoding="utf-8")

    from .audit import generer_audit
    generer_audit(tables)
    manifest = {nom: {"lignes": int(len(df)), "colonnes": list(df.columns)} for nom, df in tables.items()}
    (C.PROCESSED_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    ecarts = (ctrl.table().resultat != "OK").sum()
    print(f"\n{len(ctrl.lignes)} contrôles · {ecarts} écart(s) documenté(s) · tables écrites dans {C.PROCESSED_DIR}")


if __name__ == "__main__":
    main()
