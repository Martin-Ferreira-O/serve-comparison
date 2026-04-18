import os
from pathlib import Path

from app.config import Settings


def test_settings_loads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
    monkeypatch.setenv("COMPARISON_INVITES_PATH", "/data/invites.json")

    settings = Settings.load()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    assert settings.database_url == "postgresql://user:pass@host/db"
    assert settings.invites_path == Path("/data/invites.json")


def test_settings_defaults_port_and_paths(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("COMPARISON_INVITES_PATH", raising=False)

    settings = Settings.load()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.database_url == ""
    assert settings.invites_path == Path("data/comparison_claim_invites.json")
