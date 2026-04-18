import json
import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import create_app

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL no configurado — se omiten tests de integración",
)


@pytest.fixture(autouse=True)
def clean_db():
    yield
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute(
            "TRUNCATE participant_assessments, participant_course_attempts, "
            "sync_runs, courses, claim_invites, participants RESTART IDENTITY CASCADE"
        )


def test_health_returns_ok(tmp_path, monkeypatch):
    invites_path = tmp_path / "invites.json"
    invites_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("COMPARISON_INVITES_PATH", str(invites_path))

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "postgresql"


def test_sync_claim_flow_issues_token(tmp_path, monkeypatch):
    invites_path = tmp_path / "invites.json"
    invites_path.write_text(json.dumps({"Martin A.": "claim-martin"}), encoding="utf-8")
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
