"""Orchestriert die Diff-Berechnung zwischen Schema- und Grundriss-Anlagen."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.matching.diff import compute_diff
from app.models import (
    Anlage,
    DiffEntry,
    MatchPair,
    PlanType,
    Project,
    Task,
    TaskStatus,
    TaskType,
)

logger = logging.getLogger(__name__)


def _utc_now_naive() -> datetime:
    """Liefert die aktuelle UTC-Zeit als naive datetime (passend zur DB-Spalte)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def run_diff(db: Session, project_id: int) -> Task:
    """Erzeugt DiffEntry-Rows fuer alle vier Diff-Typen eines Projekts.

    Idempotent: bestehende DiffEntries des Projekts werden vor dem Lauf
    geloescht, da sie vollstaendig aus Anlagen + MatchPairs ableitbar sind.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Projekt {project_id} existiert nicht")

    task = Task(
        project_id=project_id,
        task_type=TaskType.diff,
        status=TaskStatus.running,
        started_at=_utc_now_naive(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id

    try:
        total_entries = _run_diff(db, project)

        task.status = TaskStatus.success
        task.progress = 1.0
        task.finished_at = _utc_now_naive()
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(
            "Diff project=%d: %d Eintraege erzeugt",
            project_id,
            total_entries,
        )
    except Exception as exc:  # noqa: BLE001 — Fehler in Task-Status festhalten
        logger.exception("Diff fehlgeschlagen")
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


def _lock_project(db: Session, project_id: int) -> None:
    """Sperrt die Project-Row, damit parallele Diff-Laeufe serialisiert werden.

    Der Lock wird bis zum Commit/Rollback der Transaktion gehalten. SQLite kennt
    kein SELECT ... FOR UPDATE; dort serialisiert bereits die Write-Transaktion
    der Datenbank selbst.
    """
    if db.bind.dialect.name == "sqlite":
        return
    db.query(Project).filter(Project.id == project_id).with_for_update().one()


def _run_diff(db: Session, project: Project) -> int:
    """Loescht alte DiffEntries und erzeugt neue aus Anlagen + MatchPairs."""
    # Serialisiert konkurrierende Laeufe, bevor bestehende Eintraege geloescht werden
    _lock_project(db, project.id)

    db.query(DiffEntry).filter(DiffEntry.project_id == project.id).delete(
        synchronize_session=False
    )

    anlagen: list[Anlage] = (
        db.query(Anlage).filter(Anlage.project_id == project.id).all()
    )
    schema = [a for a in anlagen if a.plan_type == PlanType.schema]
    grundriss = [a for a in anlagen if a.plan_type == PlanType.grundriss]

    pairs: list[MatchPair] = (
        db.query(MatchPair).filter(MatchPair.project_id == project.id).all()
    )

    results = compute_diff(schema, grundriss, pairs)
    for res in results:
        db.add(
            DiffEntry(
                project_id=project.id,
                diff_type=res.diff_type,
                severity=res.severity,
                anlage_ref_id=res.anlage_ref_id,
                partner_ref_id=res.partner_ref_id,
                details_json=res.details,
            )
        )

    db.commit()
    logger.debug(
        "Diff project=%d: %d schema, %d grundriss, %d pairs, %d diffs",
        project.id,
        len(schema),
        len(grundriss),
        len(pairs),
        len(results),
    )
    return len(results)
