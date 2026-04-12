from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    sqlite_path: Path
    invites_path: Path

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            sqlite_path=Path(
                os.getenv("COMPARISON_SQLITE_PATH", "data/comparison.sqlite3")
            ),
            invites_path=Path(
                os.getenv(
                    "COMPARISON_INVITES_PATH", "data/comparison_claim_invites.json"
                )
            ),
        )
