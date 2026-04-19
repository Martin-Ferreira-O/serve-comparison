from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    database_url: str

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            database_url=os.getenv("DATABASE_URL", ""),
        )
