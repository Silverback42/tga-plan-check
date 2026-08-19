"""Endpunkte fuer die Diff-Berechnung zwischen Schema und Grundriss."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DiffEntry, DiffType, Project, Task
from app.schemas import DiffEntryRead, DiffSummary, TaskRead
from app.services.diff_service import run_diff

router = APIRouter(tags=["diff"])


@router.post(
    "/projects/{project_id}/diff",
    response_model=TaskRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_diff(project_id: int, db: Session = Depends(get_db)) -> Task:
    """Berechnet alle Diff-Typen fuer ein Projekt.

    Laeuft im MVP synchron im Request-Handler.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return run_diff(db, project_id)


@router.get(
    "/projects/{project_id}/diff",
    response_model=list[DiffEntryRead],
)
def list_diff(
    project_id: int,
    diff_type: DiffType | None = None,
    db: Session = Depends(get_db),
) -> list[DiffEntry]:
    """Liefert die Diff-Eintraege eines Projekts, optional nach Typ gefiltert."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    query = db.query(DiffEntry).filter(DiffEntry.project_id == project_id)
    if diff_type is not None:
        query = query.filter(DiffEntry.diff_type == diff_type)
    return query.order_by(DiffEntry.diff_type, DiffEntry.id).all()


@router.get(
    "/projects/{project_id}/diff/summary",
    response_model=DiffSummary,
)
def diff_summary(project_id: int, db: Session = Depends(get_db)) -> DiffSummary:
    """Liefert die Anzahl der Diff-Eintraege je Typ."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    entries: list[DiffEntry] = (
        db.query(DiffEntry).filter(DiffEntry.project_id == project_id).all()
    )
    counts: dict[str, int] = {}
    for entry in entries:
        key = entry.diff_type.value
        counts[key] = counts.get(key, 0) + 1

    return DiffSummary(**counts, total=len(entries))
