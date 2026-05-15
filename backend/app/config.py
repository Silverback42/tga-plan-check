from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anker fuer relative Pfade: backend/ (zwei Ebenen ueber dieser Datei)
BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(value: str | Path) -> Path:
    """Macht relative Pfade absolut, bezogen auf BACKEND_ROOT."""
    path = Path(value)
    return path if path.is_absolute() else (BACKEND_ROOT / path).resolve()


class Settings(BaseSettings):
    """Anwendungskonfiguration, lesbar aus .env oder Umgebungsvariablen."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TGA Plan Check API"
    debug: bool = False

    # Datenbank: SQLite-Datei im backend/data-Ordner
    database_url: str = "sqlite:///./data/tga_plan_check.db"

    # Datei-Storage
    data_dir: Path = Path("./data")
    upload_dir: Path = Path("./data/uploads")
    report_dir: Path = Path("./data/reports")
    intermediate_dir: Path = Path("./data/intermediates")

    # Matching-Defaults
    fuzzy_threshold_default: int = Field(default=85, ge=0, le=100)

    # CORS — Frontend-Origin im Dev-Modus
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("data_dir", "upload_dir", "report_dir", "intermediate_dir")
    @classmethod
    def _resolve_dirs(cls, value: Path) -> Path:
        return _resolve_path(value)

    @field_validator("database_url")
    @classmethod
    def _resolve_sqlite_url(cls, value: str) -> str:
        # Nur SQLite-URLs mit relativem Pfad umschreiben
        prefix = "sqlite:///"
        if not value.startswith(prefix):
            return value
        raw_path = value[len(prefix):]
        # In-Memory ("sqlite:///:memory:") unveraendert lassen
        if raw_path.startswith(":"):
            return value
        if Path(raw_path).is_absolute():
            return value
        absolute = _resolve_path(raw_path)
        # SQLAlchemy erwartet POSIX-Slashes
        return f"{prefix}{absolute.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    """Cached Settings-Instanz, ermoeglicht Override in Tests."""
    return Settings()
