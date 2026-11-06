"""Construit l'archive ZIP finale de QuantAgent."""

from __future__ import annotations

import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Agentic_AI_Quantitative_Finance_FINAL.zip"
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", "_preview", "_preview_ppt", "_pptx_check"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".zip"}


def should_include(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return False
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    if path.name.startswith("~$"):
        return False
    return True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    files = [path for path in ROOT.rglob("*") if path.is_file() and should_include(path)]
    manifest = [
        "QuantAgent — Agentic AI for Quantitative Finance",
        f"Archive générée le {datetime.now(timezone.utc).isoformat()}",
        f"Fichiers : {len(files)}",
        "",
        f"{'SHA256':<64}  {'Taille':>10}  Fichier",
        "-" * 110,
    ]
    for path in sorted(files):
        relative = path.relative_to(ROOT)
        manifest.append(f"{sha256(path):<64}  {path.stat().st_size:>10}  {relative.as_posix()}")
    (ROOT / "MANIFEST.txt").write_text("\n".join(manifest), encoding="utf-8")
    files.append(ROOT / "MANIFEST.txt")

    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            archive.write(path, arcname=path.relative_to(ROOT).as_posix())
    print(OUT)
    print(f"{len(files)} fichiers · {OUT.stat().st_size/1e6:.1f} Mo")


if __name__ == "__main__":
    main()
