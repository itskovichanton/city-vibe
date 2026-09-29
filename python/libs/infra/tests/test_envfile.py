"""Корневой .env подхватывается в os.environ."""

import os
from pathlib import Path

from python.libs.infra.envfile import load_repo_env


def test_load_repo_env_does_not_override(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=from-file\nOTHER_KEY=abc\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text("# test\n", encoding="utf-8")
    (tmp_path / "python").mkdir()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "already-set")
    monkeypatch.delenv("OTHER_KEY", raising=False)

    found = load_repo_env(env_file)
    assert found == env_file
    assert os.environ["DEEPSEEK_API_KEY"] == "already-set"
    assert os.environ["OTHER_KEY"] == "abc"
