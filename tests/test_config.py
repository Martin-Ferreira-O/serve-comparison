from app.config import Settings


def test_settings_loads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")

    settings = Settings.load()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    assert settings.database_url == "postgresql://user:pass@host/db"


def test_settings_defaults_port_and_database_url(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings.load()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.database_url == ""
