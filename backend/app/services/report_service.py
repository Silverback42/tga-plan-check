"""Orchestriert den Excel-Report-Export eines Projekts."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import (
    Anlage,
    DiffEntry,
    DiffType,
    Project,
    Task,
    TaskStatus,
    TaskType,
)
from app.reporting.excel import ReportRow, build_report

logger = logging.getLogger(__name__)


def _utc_now_naive() -> datetime:
    """Liefert die aktuelle UTC-Zeit als naive datetime (passend zur DB-Spalte)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _target_path(project_id: int) -> Path:
    """Erzeugt einen kollisionsfreien Zielpfad im Report-Verzeichnis."""
    settings = get_settings()
    project_dir = settings.report_dir / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir / f"diff_report_{uuid.uuid4().hex}.xlsx"


def _to_report_row(entry: DiffEntry) -> ReportRow:
    """Denormalisiert einen DiffEntry inkl. beider Anlagen zu einer Report-Zeile."""
    anlage: Anlage | None = entry.anlage_ref
    partner: Anlage | None = entry.partner_ref

    # Bei only_grundriss steht die Grundriss-Anlage in anlage_ref,
    # bei allen anderen Typen ist anlage_ref die Schema-Anlage.
    if entry.diff_type == DiffType.only_grundriss:
        schema_anlage, grundriss_anlage = None, anlage
    else:
        schema_anlage, grundriss_anlage = anlage, partner

    gewerk = None
    for candidate in (schema_anlage, grundriss_anlage):
        if candidate is not None:
            gewerk = getattr(candidate.gewerk, "value", candidate.gewerk)
            break

    details = entry.details_json or {}
    return ReportRow(
        diff_type=entry.diff_type,
        severity=getattr(entry.severity, "value", entry.severity),
        gewerk=gewerk,
        label_schema=schema_anlage.label_raw if schema_anlage else None,
        label_grundriss=grundriss_anlage.label_raw if grundriss_anlage else None,
        raum_schema=schema_anlage.room_code if schema_anlage else None,
        raum_grundriss=grundriss_anlage.room_code if grundriss_anlage else None,
        typ_schema=schema_anlage.anlagentyp if schema_anlage else None,
        typ_grundriss=grundriss_anlage.anlagentyp if grundriss_anlage else None,
        score=details.get("score"),
        details=details,
    )


def run_report(db: Session, project_id: int) -> Task:
    """Erzeugt einen Excel-Report aus den DiffEntries eines Projekts."""
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Projekt {project_id} existiert nicht")

    task = Task(
        project_id=project_id,
        task_type=TaskType.report,
        status=TaskStatus.running,
        started_at=_utc_now_naive(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id

    try:
        entries: list[DiffEntry] = (
            db.query(DiffEntry)
            .filter(DiffEntry.project_id == project_id)
            .options(
                joinedload(DiffEntry.anlage_ref),
                joinedload(DiffEntry.partner_ref),
            )
            .order_by(DiffEntry.diff_type, DiffEntry.id)
            .all()
        )
        rows = [_to_report_row(e) for e in entries]
        target = build_report(rows, project.name, _target_path(project_id))

        task.status = TaskStatus.success
        task.progress = 1.0
        task.result_path = str(target)
        task.finished_at = _utc_now_naive()
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(
            "Report project=%d: %d Zeilen -> %s", project_id, len(rows), target
        )
    except Exception as exc:  # noqa: BLE001 — Fehler in Task-Status festhalten
        logger.exception("Report fehlgeschlagen")
        db.rollback()
        db_task = db.get(Task, task_id)
        if db_task is not None:
            db_task.status = TaskStatus.failed
            db_task.error_message = f"{type(exc).__name__}: {exc}"
            db_task.finished_at = _utc_now_naive()
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            task = db_task
        raise

    return task
