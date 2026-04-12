import os
from pathlib import Path

from app.config import Settings


def test_settings_loads_fly_style_env(monkeypatch, tmp_path):
    sqlite_path = tmp_path / "data" / "comparison.sqlite3"
    invites_path = tmp_path / "data" / "invites.json"
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("COMPARISON_SQLITE_PATH", str(sqlite_path))
    monkeypatch.setenv("COMPARISON_INVITES_PATH", str(invites_path))

    settings = Settings.load()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    assert settings.sqlite_path == sqlite_path
    assert settings.invites_path == invites_path


def test_settings_defaults_port_and_paths(monkeypatch, tmp_path):
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("COMPARISON_SQLITE_PATH", raising=False)
    monkeypatch.delenv("COMPARISON_INVITES_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    settings = Settings.load()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.sqlite_path == Path("data/comparison.sqlite3")
    assert settings.invites_path == Path("data/comparison_claim_invites.json")
