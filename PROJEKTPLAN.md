# Projektplan: TGA Plan Check (Grundriss-Schema-Abgleich)

> Abhakbare Aufgabenliste zur App-Entwicklung. Reihenfolge ist eine Empfehlung — Abhängigkeiten sind in der jeweiligen Phase erklärt.
> Detaillierter Designplan liegt unter `C:\Users\Oberh\.claude\plans\wir-haben-schon-zusammen-snazzy-forest.md`.

---

## Phase 0 — Setup & Repository

- [ ] Lokales Git-Repository in diesem Verzeichnis initialisieren
- [ ] `.gitignore` für Python + Node + Daten-Ordner anlegen
- [ ] `README.md` mit Projektbeschreibung erstellen
- [ ] Öffentliches GitHub-Repo `tga-plan-check` anlegen (über `gh`)
- [ ] Remote setzen und initialen Commit pushen (Branch `main`)
- [ ] Feature-Branch `feat/mvp-skeleton` für die ersten Arbeitsschritte anlegen
- [ ] Issue-Templates und PR-Template ergänzen (optional)

## Phase 1 — Testdaten & Domänen-Klärung

- [ ] 1–2 anonymisierte Schema-PDFs aus echtem Auftrag bereitstellen
- [ ] 1–2 zugehörige Grundriss-PDFs bereitstellen
- [ ] Beispiel-Diffs manuell ermitteln (Ground Truth für Tests)
- [ ] Synonym-Liste für HLK-Anlagen sammeln (z.B. „LTG"/„Lueftung"/„L01")
- [ ] Raum-Code-Format dokumentieren (z.B. `E.801`, `EG.124`)
- [ ] Testdaten in `backend/tests/fixtures/` ablegen (lokal, nicht committen wenn vertraulich)

## Phase 2 — Backend-Skeleton

- [x] Python-Projekt initialisieren (`pyproject.toml` oder `requirements.txt`)
- [x] Virtuelle Umgebung anlegen (`.venv`)
- [x] Dependencies installieren: fastapi, uvicorn, sqlalchemy, pydantic, pymupdf, openpyxl, rapidfuzz, python-multipart, alembic
- [x] Verzeichnisstruktur anlegen: `backend/app/{routers,services,parsers,matching,reporting,tasks}`
- [x] `backend/app/main.py` mit FastAPI-Instanz + CORS
- [x] `backend/app/config.py` mit Settings (DB-URL, Upload-Pfad, Threshold)
- [x] `backend/app/database.py` mit SQLAlchemy-Engine + Session
- [x] Health-Check-Endpunkt `GET /health`
- [x] Server lokal starten und Health-Check verifizieren

## Phase 3 — Datenmodelle

- [x] `models.py`: `Project`, `Upload`, `Task` definieren
- [x] `models.py`: `Anlage`, `MatchPair`, `DiffEntry` definieren
- [x] `schemas.py`: Pydantic Create/Read-Schemas spiegeln
- [x] Alembic initialisieren + erste Migration generieren
- [x] Migration anwenden (lokale SQLite-DB)
- [x] Smoke-Test: DB-Verbindung + leere Tabellen-Abfrage

## Phase 4 — Upload + Project Management (CRUD)

- [x] Router `projects.py`: POST/GET für Projekte
- [x] Router `uploads.py`: Multipart-Upload für PDFs
- [x] File-Storage: Dateien in `backend/data/uploads/{project_id}/` ablegen
- [x] Validation: nur PDF erlauben (MVP), Dateigröße prüfen
- [x] Einfacher curl-Test: Projekt anlegen + PDF hochladen

## Phase 5 — PDF-Extraktion (MVP-Kern)

- [ ] `parsers/pdf_anlagen.py`: PyMuPDF-Wrapper für Text + Position pro Seite
- [ ] Anlagen-Label-Extraktion via Regex (analog AKS-Export, aber gewerk-agnostisch)
- [ ] Raum-Code-Extraktion (Raumstempel-Heuristik)
- [ ] Service `extraction_service.py` orchestriert Parser pro Upload
- [ ] Router `extraction.py`: `POST /projects/{id}/extract` startet Task
- [ ] Test mit echtem Schema-PDF: extrahierte Anlagen in DB sichtbar
- [ ] Test mit echtem Grundriss-PDF: extrahierte Anlagen in DB sichtbar

## Phase 6 — Normalisierung + Fuzzy-Matching

- [ ] `matching/normalize.py`: Label-Normalisierung (lower, Whitespace, Sonderzeichen)
- [ ] `matching/normalize.py`: Synonym-Map (LTG↔Lueftung etc.)
- [ ] Unit-Tests für `normalize` mit Edge-Cases
- [ ] `matching/fuzzy.py`: rapidfuzz `process.cdist` Wrapper
- [ ] Threshold konfigurierbar pro Projekt (Default 85)
- [ ] Service `matching_service.py`: erzeugt `MatchPair`-Rows
- [ ] Router `matching.py`: `POST /projects/{id}/match`
- [ ] Test: Schema + Grundriss matchen, Score-Verteilung prüfen

## Phase 7 — Diff-Engine (4 Typen)

- [ ] `matching/diff.py`: Logik für `only_schema` (ungematchte Schema-Anlagen)
- [ ] `matching/diff.py`: Logik für `only_grundriss` (ungematchte Grundriss-Anlagen)
- [ ] `matching/diff.py`: Logik für `attr_mismatch` (matched + Attribut-Δ)
- [ ] `matching/diff.py`: Logik für `room_mismatch` (matched + Raum-Δ)
- [ ] Unit-Tests für jeden Diff-Typ mit Fixtures
- [ ] Service `diff_service.py`: erzeugt `DiffEntry`-Rows
- [ ] Router `diff.py`: `POST /projects/{id}/diff` + `GET /projects/{id}/diff`

## Phase 8 — Excel-Report

- [ ] `reporting/excel.py`: openpyxl Multi-Sheet-Export
- [ ] Sheet 1: Zusammenfassung (Counts pro Diff-Typ, Gewerk)
- [ ] Sheet 2: Nur-Schema-Anlagen
- [ ] Sheet 3: Nur-Grundriss-Anlagen
- [ ] Sheet 4: Attribut-/Raum-Diff
- [ ] Service `report_service.py` + Router `reports.py`
- [ ] Download-Endpunkt + manuelle Verifikation

## Phase 9 — Frontend-Skeleton

- [ ] Vite + React + TypeScript + Tailwind initialisieren in `frontend/`
- [ ] Router + Layout-Komponenten (Sidebar/Header)
- [ ] API-Client (`fetch` oder axios) mit TypeScript-Typen
- [ ] `ProjectListPage` + `ProjectCreatePage`
- [ ] `UploadPage` mit Drag&Drop (react-dropzone)
- [ ] `ExtractionPage` mit Tabelle der extrahierten Anlagen
- [ ] `DiffPage` mit Tabs pro Diff-Typ
- [ ] `ReportsPage` mit Excel-Download

## Phase 10 — End-to-End-Test (MVP)

- [ ] Backend + Frontend parallel laufen lassen
- [ ] Projekt anlegen → Schema + Grundriss hochladen
- [ ] Extract → Match → Diff durchklicken
- [ ] Excel-Report öffnen, Differenzen gegen Ground Truth prüfen
- [ ] Bugs in Issue-Liste sammeln
- [ ] **MVP-Pull-Request** auf `main` (über `feat/mvp-skeleton`)

---

## Phase 11+ — Erweiterungen (Post-MVP)

- [ ] DXF-Parser (`parsers/dxf_anlagen.py` via ezdxf)
- [ ] DWG-Unterstützung (ODA File Converter im Docker-Image)
- [ ] OCR-Pfad für gescannte PDFs (pytesseract + OpenCV-Preprocessing)
- [ ] Match-Review-UI: manuelles Bestätigen/Ablehnen von Match-Vorschlägen
- [ ] PDF-Overlay-Generator mit Rot/Gelb/Grün-Markern
- [ ] Side-by-Side-PDF-Viewer im Frontend (pdf.js)
- [ ] Gewerk-spezifische Synonym-Maps (HLK, ELT, SAN)
- [ ] Anlagentyp-Klassifikation per lokalem LLM (optional)
- [ ] Docker-Compose-Setup für einfaches Deployment
- [ ] Authentifizierung (wenn mehrere Nutzer)

---

## Definitionen

- **MVP** = Phasen 0 bis 10 abgeschlossen. PDF-only, HLK-only, nur "nur Schema"/"nur Grundriss"-Diff, Excel-Output, einfaches Frontend.
- **Ground Truth** = manuell ermittelte Diff-Liste, gegen die der Algorithmus validiert wird.
- **Gewerk** = TGA-Disziplin (HLK = Heizung/Lüftung/Klima, ELT = Elektrotechnik, SAN = Sanitär).
