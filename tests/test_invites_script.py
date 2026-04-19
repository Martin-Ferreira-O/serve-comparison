import os

from app.scripts import invites


def test_invites_script_loads_database_url_from_dotenv(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql://user:pass@host/db\n",
        encoding="utf-8",
    )

    captured = {}

    class FakeStore:
        def __init__(self, database_url: str):
            captured["database_url"] = database_url

        def add_claim_invite(self, display_name: str, claim_code: str) -> None:
            captured["display_name"] = display_name
            captured["claim_code"] = claim_code

    monkeypatch.setattr(invites, "ComparisonSqliteStore", FakeStore)

    exit_code = invites.main(["add", "Martin A."])

    assert exit_code == 0
    assert captured["database_url"] == "postgresql://user:pass@host/db"
    assert captured["display_name"] == "Martin A."
    assert captured["claim_code"]
    assert os.environ["DATABASE_URL"] == "postgresql://user:pass@host/db"
    assert "Participant: Martin A." in capsys.readouterr().out
