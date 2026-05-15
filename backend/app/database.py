from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Basisklasse fuer alle SQLAlchemy-Modelle."""


_settings = get_settings()

# SQLite braucht check_same_thread=False fuer FastAPI
_connect_args = (
    {"check_same_thread": False}
    if _settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    _settings.database_url,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI-Dependency: liefert eine DB-Session und schliesst sie sicher."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
