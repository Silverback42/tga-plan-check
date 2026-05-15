from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Anwendungskonfiguration, lesbar aus .env oder Umgebungsvariablen."""

    model_config = SettingsConfigDict(
        env_file=".env",
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


@lru_cache
def get_settings() -> Settings:
    """Cached Settings-Instanz, ermoeglicht Override in Tests."""
    return Settings()
