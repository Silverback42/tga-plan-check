"""Endpunkte fuer die Extraktion von Anlagen aus hochgeladenen PDFs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Anlage, PlanType, Project, Task
from app.schemas import AnlageRead, TaskRead
from app.services.extraction_service import run_extraction

router = APIRouter(tags=["extraction"])


@router.post(
    "/projects/{project_id}/extract",
    response_model=TaskRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def extract(project_id: int, db: Session = Depends(get_db)) -> Task:
    """Startet die Extraktion fuer alle Uploads eines Projekts.

    MVP: laeuft synchron im Request-Handler. Spaeter via BackgroundTasks
    oder Celery in den Hintergrund verschoben.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return run_extraction(db, project_id)


@router.get(
    "/projects/{project_id}/anlagen",
    response_model=list[AnlageRead],
)
def list_anlagen(
    project_id: int,
    plan_type: PlanType | None = None,
    db: Session = Depends(get_db),
) -> list[Anlage]:
    """Liefert die extrahierten Anlagen eines Projekts, optional gefiltert."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    query = db.query(Anlage).filter(Anlage.project_id == project_id)
    if plan_type is not None:
        query = query.filter(Anlage.plan_type == plan_type)
    return query.order_by(Anlage.page, Anlage.id).all()
