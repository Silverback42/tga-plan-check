from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import diff, extraction, matching, projects, uploads

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API fuer den Abgleich von Grundrissen und Schemas in der TGA-Planung.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # MVP hat keine Cookie-basierte Authentifizierung. Bei spaeterer Einfuehrung
    # explizit auf True schalten und Origins streng pruefen.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(uploads.router)
app.include_router(extraction.router)
app.include_router(matching.router)
app.include_router(diff.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness-Check fuer Monitoring und Smoke-Tests."""
    return {"status": "ok", "app": settings.app_name}
