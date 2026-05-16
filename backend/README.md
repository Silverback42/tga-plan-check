# Backend — TGA Plan Check

FastAPI-Backend für den Grundriss-Schema-Abgleich.

## Setup (Windows / PowerShell)

```powershell
# Vom Repo-Root aus
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

## Server starten

```powershell
# Vom backend/-Ordner aus
cd backend
..\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Health-Check: http://127.0.0.1:8000/health
API-Docs (Swagger): http://127.0.0.1:8000/docs

## Konfiguration

Werte werden über `.env` im `backend/`-Ordner überschrieben (siehe `.env.example`).

## Verzeichnisstruktur

```
backend/
├── app/
│   ├── main.py          # FastAPI-Instanz
│   ├── config.py        # Settings (pydantic-settings)
│   ├── database.py      # SQLAlchemy Engine + Session
│   ├── routers/         # API-Endpunkte
│   ├── services/        # Geschäftslogik (Orchestrierung)
│   ├── parsers/         # PDF/DXF-Extraktion
│   ├── matching/        # Normalisierung, Fuzzy-Match, Diff
│   ├── reporting/       # Excel + PDF-Overlay
│   └── tasks/           # Hintergrund-Jobs
├── tests/
├── data/                # Uploads, Reports (nicht eingecheckt)
└── requirements.txt
```
