"""Endpunkte fuer das Fuzzy-Matching zwischen Schema- und Grundriss-Anlagen."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import MatchPair, Project, Task
from app.schemas import MatchReviewItem, TaskRead
from app.services.matching_service import run_matching

router = APIRouter(tags=["matching"])


@router.post(
    "/projects/{project_id}/match",
    response_model=TaskRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_match(project_id: int, db: Session = Depends(get_db)) -> Task:
    """Erzeugt MatchPair-Rows fuer alle Schema-Grundriss-Paare ueber Threshold.

    Laeuft im MVP synchron im Request-Handler.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return run_matching(db, project_id)


@router.get(
    "/projects/{project_id}/matches",
    response_model=list[MatchReviewItem],
)
def list_matches(
    project_id: int,
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
) -> list[MatchReviewItem]:
    """Liefert alle MatchPairs eines Projekts mit beiden Anlagen-Details."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    pairs: list[MatchPair] = (
        db.query(MatchPair)
        .filter(
            MatchPair.project_id == project_id,
            MatchPair.score >= min_score,
        )
        .options(
            joinedload(MatchPair.schema_anlage),
            joinedload(MatchPair.grundriss_anlage),
        )
        .order_by(MatchPair.score.desc(), MatchPair.id)
        .all()
    )

    return [
        MatchReviewItem(
            match=pair,
            schema_anlage=pair.schema_anlage,
            grundriss_anlage=pair.grundriss_anlage,
        )
        for pair in pairs
    ]
