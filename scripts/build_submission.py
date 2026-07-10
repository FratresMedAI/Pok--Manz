"""Build a Kaggle-compatible submission.tar.gz."""

from __future__ import annotations

import shutil
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "artifacts" / "submission_build"
OUT = ROOT / "artifacts" / "submission.tar.gz"


def copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main() -> None:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    for path in (ROOT / "submission").iterdir():
        if path.is_file() and path.name != "__pycache__":
            shutil.copy2(path, BUILD_DIR / path.name)
    copytree(ROOT / "vendor" / "cabt_sample_submission" / "cg", BUILD_DIR / "cg")
    copytree(ROOT / "src", BUILD_DIR / "src")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    with tarfile.open(OUT, "w:gz") as archive:
        for path in BUILD_DIR.rglob("*"):
            archive.add(path, arcname=path.relative_to(BUILD_DIR))

    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

