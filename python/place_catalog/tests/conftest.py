"""Фикстуры place-catalog tests."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLACE_SRC = Path(__file__).resolve().parents[1] / "src"
SITE = Path("/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages")

for p in (REPO_ROOT, PLACE_SRC, SITE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
