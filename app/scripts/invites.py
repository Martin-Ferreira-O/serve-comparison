from __future__ import annotations

import argparse
import os
from pathlib import Path
import secrets
import sys

from app.config import Settings
from app.persistence.comparison_sqlite_store import ComparisonSqliteStore


def _load_dotenv() -> None:
    current = Path.cwd().resolve()
    env_path = None

    for directory in (current, *current.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            env_path = candidate
            break

    if env_path is None:
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].lstrip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage comparison claim invites stored in Postgres."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser(
        "add", help="Create or replace a pending invite for a participant"
    )
    add_parser.add_argument("display_name", help="Participant display name")

    return parser


def _generate_claim_code() -> str:
    return secrets.token_urlsafe(12)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    _load_dotenv()
    settings = Settings.load()
    if not settings.database_url:
        print("DATABASE_URL is not configured.", file=sys.stderr)
        return 1

    if args.command != "add":
        parser.print_help()
        return 1

    display_name = args.display_name.strip()
    if not display_name:
        print("display_name cannot be empty.", file=sys.stderr)
        return 1

    claim_code = _generate_claim_code()
    store = ComparisonSqliteStore(settings.database_url)

    try:
        store.add_claim_invite(display_name, claim_code)
    except PermissionError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(f"Participant: {display_name}")
    print(f"Pass: {claim_code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
