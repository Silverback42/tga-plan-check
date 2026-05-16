import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

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

    # CORS — leer per Default; muss pro Umgebung explizit gesetzt werden.
    # Wildcard "*" wird abgewiesen, weil wir CORS in Verbindung mit anderen
    # Features (z.B. spaeter Auth) sicher gestalten muessen.
    cors_origins: list[str] = []

    @field_validator("data_dir", "upload_dir", "report_dir", "intermediate_dir")
    @classmethod
    def _resolve_dirs(cls, value: Path) -> Path:
        return _resolve_path(value)

    @field_validator("database_url")
    @classmethod
    def _resolve_sqlite_url(cls, value: str) -> str:
        # Nur SQLite-URLs mit relativem Pfad umschreiben (case-insensitive,
        # damit "SQLite:///" oder "SQLITE:///" ebenfalls erkannt werden)
        if not value.lower().startswith("sqlite:///"):
            return value
        prefix_len = len("sqlite:///")
        raw_path = value[prefix_len:]
        # In-Memory ("sqlite:///:memory:") unveraendert lassen
        if raw_path.startswith(":"):
            return value
        if Path(raw_path).is_absolute():
            return value
        absolute = _resolve_path(raw_path)
        # SQLAlchemy erwartet POSIX-Slashes
        return f"sqlite:///{absolute.as_posix()}"

    @field_validator("cors_origins")
    @classmethod
    def _reject_wildcard(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError(
                "cors_origins darf '*' nicht enthalten (Konflikt mit credentials)."
            )
        return value

    @model_validator(mode="after")
    def _ensure_directories_exist(self) -> "Settings":
        for directory in (
            self.data_dir,
            self.upload_dir,
            self.report_dir,
            self.intermediate_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self

    @model_validator(mode="after")
    def _warn_localhost_in_production(self) -> "Settings":
        if not self.debug:
            unsafe = [
                o
                for o in self.cors_origins
                if "localhost" in o or "127.0.0.1" in o
            ]
            if unsafe:
                logger.warning(
                    "Production-Konfiguration enthaelt Localhost-Origins in "
                    "cors_origins: %s",
                    unsafe,
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached Settings-Instanz, ermoeglicht Override in Tests."""
    return Settings()
