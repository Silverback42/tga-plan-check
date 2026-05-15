# TGA Plan Check

Web-Anwendung zum automatischen Abgleich von **Grundrissen und Schemas** in der TGA-Planung. Identifiziert Differenzen wie fehlende oder widersprüchliche Anlagen, um die Planqualität bei neuen Aufträgen früh zu prüfen.

## Status

🚧 In Entwicklung — siehe [PROJEKTPLAN.md](./PROJEKTPLAN.md) für aktuellen Fortschritt.

## Idee

Beim Empfang neuer Projekt-Unterlagen weichen Schemata und Grundrisse oft voneinander ab:

- Anlage im Schema dokumentiert, aber im Grundriss nicht eingezeichnet
- Anlage im Grundriss eingezeichnet, aber im Schema nicht aufgeführt
- Abweichende Attribute oder Raumzuordnungen zwischen beiden Plänen

Diese App lädt Schema und Grundriss hoch, gleicht beide automatisch ab und liefert einen Differenz-Report (Excel + annotierte PDF).

## Geplante Features (MVP)

- Upload von Schema- und Grundriss-PDFs
- Automatische Extraktion der Anlagen-Bezeichnungen und Positionen
- Fuzzy-Matching nach Anlagentyp/-bezeichnung
- Differenz-Erkennung: nur Schema / nur Grundriss / abweichende Attribute / Raumzuordnung
- Excel-Report mit allen Differenzen

## Geplante Features (Post-MVP)

- DWG/DXF-Unterstützung
- OCR für gescannte Pläne
- Visueller Side-by-Side-PDF-Viewer mit Markierungen
- Manuelles Review und Korrektur der Match-Vorschläge

## Tech-Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, PyMuPDF, rapidfuzz, openpyxl
- **Frontend:** Vite + React + TypeScript + Tailwind CSS
- **DB:** SQLite (lokal), optional PostgreSQL

## Setup

Wird ergänzt sobald die Skeleton-Phase abgeschlossen ist.

## Gewerke (Scope)

Heizung/Lüftung/Klima (HLK), Elektrotechnik (ELT), Sanitär (SAN).
