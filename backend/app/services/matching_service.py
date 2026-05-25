"""Orchestriert das Fuzzy-Matching zwischen Schema- und Grundriss-Anlagen."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from itertools import groupby

from sqlalchemy.orm import Session

from app.matching.fuzzy import match_anlagen
from app.models import (
    Anlage,
    Gewerk,
    MatchPair,
    MatchStatus,
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


def run_matching(db: Session, project_id: int) -> Task:
    """Erzeugt MatchPair-Rows fuer alle gewerk-konsistenten Paare ueber Threshold.

    Idempotent: bestehende MatchPairs mit status=auto werden vor dem Lauf
    geloescht, manuell bestaetigte/verworfene bleiben erhalten.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Projekt {project_id} existiert nicht")

    task = Task(
        project_id=project_id,
        task_type=TaskType.match,
        status=TaskStatus.running,
        started_at=_utc_now_naive(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id

    try:
        total_pairs = _run_matching(db, project)

        task.status = TaskStatus.success
        task.progress = 1.0
        task.finished_at = _utc_now_naive()
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(
            "Matching project=%d: %d Kandidaten erzeugt",
            project_id,
            total_pairs,
        )
    except Exception as exc:  # noqa: BLE001 — Fehler in Task-Status festhalten
        logger.exception("Matching fehlgeschlagen")
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


def _run_matching(db: Session, project: Project) -> int:
    """Loescht alte auto-Pairs und erzeugt neue, gruppiert nach Gewerk."""
    # Nur status=auto entfernen, damit manuelle Reviews erhalten bleiben
    db.query(MatchPair).filter(
        MatchPair.project_id == project.id,
        MatchPair.status == MatchStatus.auto,
    ).delete(synchronize_session=False)

    anlagen: list[Anlage] = (
        db.query(Anlage).filter(Anlage.project_id == project.id).all()
    )
    threshold = project.fuzzy_threshold

    total = 0
    for gewerk, group in _group_by_gewerk(anlagen):
        schema = [a for a in group if a.plan_type == PlanType.schema]
        grundriss = [a for a in group if a.plan_type == PlanType.grundriss]
        if not schema or not grundriss:
            continue

        candidates = match_anlagen(schema, grundriss, threshold)
        for cand in candidates:
            db.add(
                MatchPair(
                    project_id=project.id,
                    schema_anlage_id=cand.schema_id,
                    grundriss_anlage_id=cand.grundriss_id,
                    score=cand.score,
                    method=cand.method,
                    status=MatchStatus.auto,
                )
            )
        total += len(candidates)
        logger.debug(
            "Matching gewerk=%s: %d schema, %d grundriss, %d candidates",
            gewerk.value,
            len(schema),
            len(grundriss),
            len(candidates),
        )

    db.commit()
    return total


def _group_by_gewerk(anlagen: list[Anlage]) -> list[tuple[Gewerk, list[Anlage]]]:
    """Gruppiert Anlagen nach Gewerk (stabil)."""
    sorted_anlagen = sorted(anlagen, key=lambda a: a.gewerk.value)
    return [
        (gewerk, list(group))
        for gewerk, group in groupby(sorted_anlagen, key=lambda a: a.gewerk)
    ]
