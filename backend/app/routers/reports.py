"""Endpunkte fuer die Erzeugung und den Download von Excel-Reports."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Project, Task, TaskStatus, TaskType
from app.schemas import TaskRead
from app.services.report_service import run_report

router = APIRouter(tags=["reports"])

_XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@router.post("/projects/{project_id}/report", response_model=TaskRead)
def create_report(project_id: int, db: Session = Depends(get_db)) -> Task:
    """Erzeugt einen Excel-Report aus den vorhandenen Diff-Eintraegen.

    Laeuft im MVP synchron im Request-Handler.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return run_report(db, project_id)


def _latest_report_task(db: Session, project_id: int) -> Task | None:
    """Liefert den juengsten erfolgreichen Report-Task eines Projekts."""
    return (
        db.query(Task)
        .filter(
            Task.project_id == project_id,
            Task.task_type == TaskType.report,
            Task.status == TaskStatus.success,
        )
        .order_by(Task.id.desc())
        .first()
    )


def _resolve_within_report_dir(raw_path: str) -> Path:
    """Prueft, dass der gespeicherte Pfad im Report-Verzeichnis liegt.

    Schuetzt davor, dass ein manipulierter result_path beliebige Dateien
    ausliefert (Path-Traversal).
    """
    report_dir = get_settings().report_dir.resolve()
    candidate = Path(raw_path).resolve()
    if not candidate.is_relative_to(report_dir):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report-Pfad liegt ausserhalb des Report-Verzeichnisses.",
        )
    return candidate


@router.get("/projects/{project_id}/report/download")
def download_report(project_id: int, db: Session = Depends(get_db)) -> FileResponse:
    """Liefert den zuletzt erzeugten Excel-Report als Datei-Download."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    task = _latest_report_task(db, project_id)
    if task is None or not task.result_path:
        raise HTTPException(
            status_code=404,
            detail="Kein Report vorhanden — bitte zuerst POST /report aufrufen.",
        )

    path = _resolve_within_report_dir(task.result_path)
    if not path.is_file():
        raise HTTPException(
            status_code=410,
            detail="Report-Datei existiert nicht mehr — bitte neu erzeugen.",
        )

    return FileResponse(
        path=path,
        media_type=_XLSX_MEDIA_TYPE,
        filename=f"diff_report_projekt_{project_id}.xlsx",
    )
