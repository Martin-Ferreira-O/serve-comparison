import json

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_exposes_sqlite_path(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPARISON_SQLITE_PATH", str(tmp_path / "comparison.sqlite3"))
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["sqlite_path"] == str(tmp_path / "comparison.sqlite3")


def test_sync_claim_flow_issues_token(tmp_path, monkeypatch):
    invites_path = tmp_path / "invites.json"
    invites_path.write_text(json.dumps({"Martin A.": "claim-martin"}), encoding="utf-8")
    monkeypatch.setenv("COMPARISON_SQLITE_PATH", str(tmp_path / "comparison.sqlite3"))
    monkeypatch.setenv("COMPARISON_INVITES_PATH", str(invites_path))

    client = TestClient(create_app())
    response = client.post(
        "/api/comparison/sync",
        json={
            "participant_name": "Martin A.",
            "claim_code": "claim-martin",
            "courses": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["state"] == "linked"
    assert response.json()["issued_sync_token"]


def test_sync_rejects_invalid_claim_code(tmp_path, monkeypatch):
    invites_path = tmp_path / "invites.json"
    invites_path.write_text(json.dumps({"Martin A.": "claim-martin"}), encoding="utf-8")
    monkeypatch.setenv("COMPARISON_SQLITE_PATH", str(tmp_path / "comparison.sqlite3"))
    monkeypatch.setenv("COMPARISON_INVITES_PATH", str(invites_path))

    client = TestClient(create_app())
    response = client.post(
        "/api/comparison/sync",
        json={
            "participant_name": "Martin A.",
            "claim_code": "wrong-code",
            "courses": [],
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "claim_invite_invalid"}
