"""Orchestriert die Extraktion von Anlagen aus hochgeladenen PDFs."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.matching.normalize import normalize_label
from app.models import Anlage, Project, Task, TaskStatus, TaskType, Upload
from app.parsers.pdf_anlagen import extract_anlagen

logger = logging.getLogger(__name__)


def _room_patterns_from_project(project: Project) -> list[str] | None:
    """Liest projekt-spezifische Raum-Regex-Patterns aus synonyms_json."""
    cfg = project.synonyms_json or {}
    patterns = cfg.get("room_patterns") if isinstance(cfg, dict) else None
    if isinstance(patterns, list) and patterns:
        return [str(p) for p in patterns]
    return None


def run_extraction(db: Session, project_id: int) -> Task:
    """Fuehrt die Extraktion fuer alle Uploads eines Projekts synchron aus.

    Erzeugt einen Task-Datensatz und liefert ihn nach Abschluss zurueck.
    Bereits existierende Anlagen-Rows zu den Uploads werden vorher geloescht,
    damit Re-Runs idempotent sind.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Projekt {project_id} existiert nicht")

    task = Task(
        project_id=project_id,
        task_type=TaskType.extract,
        status=TaskStatus.running,
        started_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        room_patterns = _room_patterns_from_project(project)
        synonyms = (
            project.synonyms_json.get("labels")
            if isinstance(project.synonyms_json, dict)
            else None
        )

        uploads: list[Upload] = (
            db.query(Upload).filter(Upload.project_id == project_id).all()
        )
        total_anlagen = _process_uploads(db, uploads, room_patterns, synonyms)

        task.status = TaskStatus.success
        task.progress = 1.0
        task.finished_at = datetime.utcnow()
        task.result_path = None
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(
            "Extraction project=%d: %d Anlagen aus %d Uploads",
            project_id,
            total_anlagen,
            len(uploads),
        )
    except Exception as exc:  # noqa: BLE001 — Fehler in Task-Status festhalten
        logger.exception("Extraction fehlgeschlagen")
        task.status = TaskStatus.failed
        task.error_message = f"{type(exc).__name__}: {exc}"
        task.finished_at = datetime.utcnow()
        db.add(task)
        db.commit()
        db.refresh(task)
        raise

    return task


def _process_uploads(
    db: Session,
    uploads: list[Upload],
    room_patterns: list[str] | None,
    synonyms: dict[str, str] | None,
) -> int:
    """Verarbeitet alle Uploads, ersetzt deren bestehende Anlagen-Rows."""
    total = 0
    for upload in uploads:
        # idempotent: alte Rows entfernen
        db.query(Anlage).filter(Anlage.upload_id == upload.id).delete()

        pdf_path = Path(upload.file_path)
        if not pdf_path.exists():
            logger.warning("Datei fehlt: %s", pdf_path)
            continue

        extracted = extract_anlagen(pdf_path, room_patterns=room_patterns)
        for ext in extracted:
            db.add(
                Anlage(
                    project_id=upload.project_id,
                    upload_id=upload.id,
                    plan_type=upload.plan_type,
                    gewerk=upload.gewerk,
                    label_raw=ext.label_raw,
                    label_normalized=normalize_label(
                        ext.attributes.get("normalized") or ext.label_raw,
                        synonyms,
                    ),
                    anlagentyp=ext.anlagentyp,
                    room_code=ext.room_code,
                    page=ext.page,
                    x=ext.x,
                    y=ext.y,
                    attributes_json=ext.attributes,
                )
            )
        total += len(extracted)

    db.commit()
    return total
