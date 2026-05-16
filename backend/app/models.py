"""SQLAlchemy-Modelle fuer die TGA-Plan-Check-Anwendung."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# Enums --------------------------------------------------------------------


class PlanType(str, enum.Enum):
    schema = "schema"
    grundriss = "grundriss"


class SourceType(str, enum.Enum):
    pdf_vector = "pdf_vector"
    pdf_scan = "pdf_scan"
    dxf = "dxf"
    dwg = "dwg"


class Gewerk(str, enum.Enum):
    HLK = "HLK"
    ELT = "ELT"
    SAN = "SAN"


class TaskType(str, enum.Enum):
    extract = "extract"
    match = "match"
    diff = "diff"
    report = "report"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class MatchStatus(str, enum.Enum):
    auto = "auto"
    confirmed = "confirmed"
    rejected = "rejected"
    manual = "manual"


class DiffType(str, enum.Enum):
    only_schema = "only_schema"
    only_grundriss = "only_grundriss"
    attr_mismatch = "attr_mismatch"
    room_mismatch = "room_mismatch"


class Severity(str, enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"


# Modelle ------------------------------------------------------------------


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gewerk_scope: Mapped[list[str]] = mapped_column(JSON, default=list)
    fuzzy_threshold: Mapped[int] = mapped_column(Integer, default=85)
    synonyms_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    uploads: Mapped[list[Upload]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[list[Task]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    anlagen: Mapped[list[Anlage]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    match_pairs: Mapped[list[MatchPair]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    diff_entries: Mapped[list[DiffEntry]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False), nullable=False
    )
    plan_type: Mapped[PlanType] = mapped_column(
        Enum(PlanType, native_enum=False), nullable=False
    )
    gewerk: Mapped[Gewerk] = mapped_column(
        Enum(Gewerk, native_enum=False), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="uploads")
    anlagen: Mapped[list[Anlage]] = relationship(
        back_populates="upload", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, native_enum=False), nullable=False
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False), default=TaskStatus.pending, nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    result_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="tasks")


class Anlage(Base):
    """Eine im Plan erkannte Anlage (z.B. Lueftungsgeraet, Pumpe, Verteiler)."""

    __tablename__ = "anlagen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_id: Mapped[int] = mapped_column(
        ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_type: Mapped[PlanType] = mapped_column(
        Enum(PlanType, native_enum=False), nullable=False, index=True
    )
    gewerk: Mapped[Gewerk] = mapped_column(
        Enum(Gewerk, native_enum=False), nullable=False
    )

    label_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    label_normalized: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    anlagentyp: Mapped[str | None] = mapped_column(String(128), nullable=True)
    room_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)

    attributes_json: Mapped[dict] = mapped_column(JSON, default=dict)
    aks: Mapped[str | None] = mapped_column(String(128), nullable=True)

    project: Mapped[Project] = relationship(back_populates="anlagen")
    upload: Mapped[Upload] = relationship(back_populates="anlagen")


class MatchPair(Base):
    """Ein vorgeschlagenes oder bestaetigtes Match zwischen Schema- und Grundriss-Anlage."""

    __tablename__ = "match_pairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    schema_anlage_id: Mapped[int] = mapped_column(
        ForeignKey("anlagen.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grundriss_anlage_id: Mapped[int] = mapped_column(
        ForeignKey("anlagen.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(64), default="fuzzy_token_sort")
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, native_enum=False), default=MatchStatus.auto, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="match_pairs")
    schema_anlage: Mapped[Anlage] = relationship(foreign_keys=[schema_anlage_id])
    grundriss_anlage: Mapped[Anlage] = relationship(foreign_keys=[grundriss_anlage_id])


class DiffEntry(Base):
    """Ein erkannter Unterschied zwischen Schema und Grundriss."""

    __tablename__ = "diff_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    diff_type: Mapped[DiffType] = mapped_column(
        Enum(DiffType, native_enum=False), nullable=False, index=True
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False), default=Severity.warning, nullable=False
    )
    # Hauptreferenz auf eine Anlage (z.B. die nur-im-Schema vorhandene)
    anlage_ref_id: Mapped[int | None] = mapped_column(
        ForeignKey("anlagen.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Optionale Partner-Anlage bei attr_mismatch / room_mismatch
    partner_ref_id: Mapped[int | None] = mapped_column(
        ForeignKey("anlagen.id", ondelete="CASCADE"), nullable=True
    )
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="diff_entries")
    anlage_ref: Mapped[Anlage | None] = relationship(foreign_keys=[anlage_ref_id])
    partner_ref: Mapped[Anlage | None] = relationship(foreign_keys=[partner_ref_id])
