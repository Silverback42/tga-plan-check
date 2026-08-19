"""Tests fuer die Report-Endpunkte (Pfad-Absicherung, Fehlerfaelle)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.routers.reports import _resolve_within_report_dir


def test_pfad_im_report_verzeichnis_wird_akzeptiert():
    target = get_settings().report_dir / "1" / "report.xlsx"

    resolved = _resolve_within_report_dir(str(target))

    assert resolved.name == "report.xlsx"


def test_absoluter_pfad_ausserhalb_wird_abgewiesen():
    with pytest.raises(HTTPException) as exc:
        _resolve_within_report_dir("C:/Windows/win.ini")

    assert exc.value.status_code == 403


def test_traversal_ueber_parent_wird_abgewiesen():
    outside = get_settings().report_dir / ".." / "uploads" / "geheim.pdf"

    with pytest.raises(HTTPException) as exc:
        _resolve_within_report_dir(str(outside))

    assert exc.value.status_code == 403
