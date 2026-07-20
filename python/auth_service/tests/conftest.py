"""Фикстуры auth-service tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

AUTH_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTH_ROOT.parents[1]
AUTH_SRC = AUTH_ROOT / "src"
SITE = Path("/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages")

os.chdir(AUTH_ROOT)
os.environ.setdefault("PROFILE", "dev")

for p in (REPO_ROOT, AUTH_SRC, SITE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Регистрация IoC-бинов до импорта AuthUseCaseImpl в тестах
import python.libs.clients.domain.user_service.client  # noqa: E402,F401
import python.auth_service.src.auth_service.infra.otp_store  # noqa: E402,F401
import python.auth_service.src.auth_service.repo.account  # noqa: E402,F401
