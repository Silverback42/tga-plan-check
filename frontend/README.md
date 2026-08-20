# TGA Plan Check — Frontend

React-Oberflaeche fuer den Abgleich von TGA-Schemas und Grundrissen. Die
Anwendung ist eine reine Client-App; alle Daten kommen aus dem FastAPI-Backend
in `../backend`.

## Voraussetzungen

- Node.js 20 oder neuer
- Laufendes Backend auf `http://127.0.0.1:8000` (siehe `../README.md`)

## Backend-Anbindung

Der Vite-Dev-Server proxied `/api` an das Backend und entfernt dabei das
Prefix (siehe `vite.config.ts`) — im Browser ist deshalb keine
CORS-Konfiguration noetig. Fuer abweichende Deployments laesst sich die
Basis-URL ueber die Umgebungsvariable `VITE_API_BASE_URL` setzen; ohne
Angabe wird `/api` verwendet.

## Routen

| Pfad | Seite |
| --- | --- |
| `/` | Projektliste |
| `/projects/new` | Neues Projekt anlegen |
| `/projects/:projectId/uploads` | Plaene hochladen |
| `/projects/:projectId/anlagen` | Extrahierte Anlagen |
| `/projects/:projectId/diff` | Matching und Abgleich |
| `/projects/:projectId/report` | Excel-Report erzeugen und laden |

Unbekannte Pfade leiten auf die Projektliste um. Routen mit ungueltiger
`projectId` zeigen einen Hinweis statt eine Anfrage mit `NaN` zu senden.

## Befehle

```bash
npm install      # Abhaengigkeiten installieren
npm run dev      # Dev-Server mit HMR
npm run build    # Typpruefung (tsc -b) und Produktions-Build
npm run lint     # Oxlint
npm run preview  # Produktions-Build lokal ausliefern
```

`npm run build` und `npm run lint` sind die Pruefungen, die vor jedem Commit
laufen sollten.
