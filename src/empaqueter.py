"""Assemble les livrables dans outputs/ : archive autonome du tableau de bord et documents.

Usage : python -m src.empaqueter
"""
from __future__ import annotations

import shutil
import zipfile

from . import config as C

ARCHIVE = C.OUTPUTS_DIR / "dashboard_inclusion_togo.zip"
RACINE_ZIP = "dashboard_inclusion_togo"
INCLURE = ["app.py", "README.md", "requirements.txt", "data_dictionary.md", "methodologie_et_limites.md"]
DOSSIERS = ["pages", "src", "assets", "data", "data_processed", "tests", ".streamlit"]
DOCS = ["README.md", "requirements.txt", "data_dictionary.md", "methodologie_et_limites.md"]


def main() -> None:
    C.OUTPUTS_DIR.mkdir(exist_ok=True)
    geo = next((p for p in C.DEFI1_GEOMETRY_CANDIDATES if p.exists()), None)
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as z:
        for f in INCLURE:
            z.write(C.ROOT / f, f"{RACINE_ZIP}/{f}")
        for d in DOSSIERS:
            for p in sorted((C.ROOT / d).rglob("*")):
                if p.is_file() and "__pycache__" not in p.parts:
                    z.write(p, f"{RACINE_ZIP}/{p.relative_to(C.ROOT).as_posix()}")
        if geo:
            z.write(geo, f"{RACINE_ZIP}/data_defi1/prefectures.gpkg")
    for f in DOCS:
        shutil.copy2(C.ROOT / f, C.OUTPUTS_DIR / f)
    print(f"{ARCHIVE} ({ARCHIVE.stat().st_size / 1e6:.1f} Mo)")


if __name__ == "__main__":
    main()
