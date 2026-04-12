from fastapi.testclient import TestClient

from app.main import create_app


def test_dashboard_page_renders(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPARISON_SQLITE_PATH", str(tmp_path / "comparison.sqlite3"))
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Dashboard de comparacion" in response.text


def test_dashboard_page_serves_comparison_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPARISON_SQLITE_PATH", str(tmp_path / "comparison.sqlite3"))
    client = TestClient(create_app())

    response = client.get("/")

    assert "styles.css" in response.text
    assert "comparison.css" in response.text
    assert "comparison.js" in response.text
