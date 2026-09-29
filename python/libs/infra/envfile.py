"""Корневой `.env` → os.environ. Уже заданные переменные не перетирает."""

from __future__ import annotations

import os
from pathlib import Path


def load_repo_env(start: Path | None = None) -> Path | None:
    here = (start or Path(__file__)).resolve()
    for folder in [here.parent, *here.parents]:
        candidate = folder / ".env"
        if candidate.is_file():
            _apply(candidate)
            return candidate
        if (folder / "Makefile").is_file() and (folder / "python").is_dir():
            break
    return None


def _apply(path: Path) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val
