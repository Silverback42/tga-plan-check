"""Pydantic-Schemas fuer Request/Response-Bodies der API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    DiffType,
    Gewerk,
    MatchStatus,
    PlanType,
    Severity,
    SourceType,
    TaskStatus,
    TaskType,
)


# Project ------------------------------------------------------------------


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    project_code: str | None = Field(default=None, max_length=64)
    gewerk_scope: list[Gewerk] = Field(default_factory=list)
    fuzzy_threshold: int = Field(default=85, ge=0, le=100)
    synonyms_json: dict = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    project_code: str | None = Field(default=None, max_length=64)
    gewerk_scope: list[Gewerk] | None = None
    fuzzy_threshold: int | None = Field(default=None, ge=0, le=100)
    synonyms_json: dict | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# Upload -------------------------------------------------------------------


class UploadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    filename: str
    source_type: SourceType
    plan_type: PlanType
    gewerk: Gewerk
    # file_path bewusst nicht exponiert — interner Pfad bleibt im Modell.
    file_size: int | None
    uploaded_at: datetime


# Task ---------------------------------------------------------------------


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    task_type: TaskType
    status: TaskStatus
    progress: float
    result_path: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


# Anlage -------------------------------------------------------------------


class AnlageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    upload_id: int
    plan_type: PlanType
    gewerk: Gewerk
    label_raw: str
    label_normalized: str
    anlagentyp: str | None
    room_code: str | None
    page: int | None
    x: float | None
    y: float | None
    attributes_json: dict
    aks: str | None


# Match --------------------------------------------------------------------


class MatchPairRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    schema_anlage_id: int
    grundriss_anlage_id: int
    score: float
    method: str
    status: MatchStatus
    created_at: datetime


class MatchReviewItem(BaseModel):
    """Aggregierte Sicht fuer das Review-UI: Match + beide Anlagen."""

    match: MatchPairRead
    schema_anlage: AnlageRead
    grundriss_anlage: AnlageRead


class MatchUpdate(BaseModel):
    status: MatchStatus


# Diff ---------------------------------------------------------------------


class DiffEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    diff_type: DiffType
    severity: Severity
    anlage_ref_id: int | None
    partner_ref_id: int | None
    details_json: dict
    created_at: datetime


class DiffSummary(BaseModel):
    """Aggregierte Zaehlung pro Diff-Typ fuer die Uebersichtsseite."""

    only_schema: int = 0
    only_grundriss: int = 0
    attr_mismatch: int = 0
    room_mismatch: int = 0
    total: int = 0
