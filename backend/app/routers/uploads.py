"""Endpunkte fuer Datei-Uploads (Schema/Grundriss-PDFs)."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Gewerk, PlanType, Project, SourceType, Upload
from app.schemas import UploadRead

router = APIRouter(prefix="/projects/{project_id}/uploads", tags=["uploads"])

# MVP: maximale Dateigroesse 50 MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024
_CHUNK_SIZE = 1024 * 1024
_PDF_MAGIC = b"%PDF-"
# Erlaubte Content-Types — octet-stream und None werden toleriert, weil viele Clients
# (z.B. PowerShell, einige Browser) PDFs ohne korrekten Mimetype hochladen.
# Magic-Byte-Check (siehe _validate_pdf) verhindert Spoofing per Dateiname.
ACCEPTED_PDF_MIMES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
    "binary/octet-stream",
    None,
    "",
}


def _validate_pdf(file: UploadFile) -> None:
    """Validiert Dateiname, Content-Type und PDF-Magic-Bytes."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dateiname muss auf .pdf enden.",
        )
    if file.content_type not in ACCEPTED_PDF_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Content-Type {file.content_type!r} ist nicht erlaubt. "
                "MVP akzeptiert nur PDF."
            ),
        )

    # Magic-Bytes-Check: PDFs beginnen mit "%PDF-"
    header = file.file.read(len(_PDF_MAGIC))
    file.file.seek(0)
    if not header.startswith(_PDF_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Datei enthaelt keine gueltige PDF-Signatur.",
        )


def _target_path(project_id: int, original_name: str) -> Path:
    """Erzeugt einen kollisionsfreien Zielpfad unterhalb des Upload-Verzeichnisses."""
    settings = get_settings()
    project_dir = settings.upload_dir / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_name).suffix or ".pdf"
    unique_id = uuid.uuid4().hex
    return project_dir / f"{unique_id}{suffix}"


@router.post("", response_model=UploadRead, status_code=status.HTTP_201_CREATED)
def upload_plan(
    project_id: int,
    plan_type: PlanType = Form(...),
    gewerk: Gewerk = Form(...),
    source_type: SourceType = Form(default=SourceType.pdf_vector),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Upload:
    """Lädt einen Plan (PDF) hoch und legt einen Upload-Datensatz an."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    _validate_pdf(file)

    target = _target_path(project_id, file.filename or "upload.pdf")
    file_size = 0
    try:
        with target.open("wb") as out:
            while True:
                chunk = file.file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_UPLOAD_SIZE:
                    out.close()
                    target.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            f"Datei ueberschreitet das Limit von "
                            f"{MAX_UPLOAD_SIZE} Bytes."
                        ),
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except OSError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Datei konnte nicht gespeichert werden: {exc}",
        ) from exc
    finally:
        file.file.close()

    upload = Upload(
        project_id=project_id,
        filename=file.filename or target.name,
        source_type=source_type,
        plan_type=plan_type,
        gewerk=gewerk,
        file_path=str(target),
        file_size=file_size,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


@router.get("", response_model=list[UploadRead])
def list_uploads(project_id: int, db: Session = Depends(get_db)) -> list[Upload]:
    """Liefert alle Uploads eines Projekts."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return (
        db.query(Upload)
        .filter(Upload.project_id == project_id)
        .order_by(Upload.uploaded_at.desc())
        .all()
    )
