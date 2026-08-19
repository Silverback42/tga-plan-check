"""Unit-Tests fuer die Diff-Engine (4 Diff-Typen)."""

from __future__ import annotations

from dataclasses import dataclass

from app.matching.diff import (
    compute_diff,
    find_attr_mismatch,
    find_only_grundriss,
    find_only_schema,
    find_room_mismatch,
)
from app.models import DiffType, Gewerk, Severity


@dataclass(slots=True)
class _StubAnlage:
    """Minimaler Stub mit den Attributen, die die Diff-Logik liest."""

    id: int
    label_raw: str = "RLT 01"
    gewerk: Gewerk = Gewerk.HLK
    anlagentyp: str | None = None
    room_code: str | None = None


@dataclass(slots=True)
class _StubPair:
    """Minimaler Stub fuer ein MatchPair."""

    schema_anlage_id: int
    grundriss_anlage_id: int
    score: float = 100.0
    status: str = "auto"


def _by_type(results, diff_type: DiffType):
    return [r for r in results if r.diff_type == diff_type]


# only_schema --------------------------------------------------------------


def test_only_schema_findet_ungematchte():
    schema = [_StubAnlage(id=1), _StubAnlage(id=2)]

    results = find_only_schema(schema, matched_schema_ids={1})

    assert len(results) == 1
    assert results[0].anlage_ref_id == 2
    assert results[0].diff_type == DiffType.only_schema
    assert results[0].severity == Severity.error


def test_only_schema_leer_wenn_alle_gematcht():
    schema = [_StubAnlage(id=1), _StubAnlage(id=2)]

    assert find_only_schema(schema, matched_schema_ids={1, 2}) == []


# only_grundriss -----------------------------------------------------------


def test_only_grundriss_findet_ungematchte():
    grundriss = [_StubAnlage(id=101), _StubAnlage(id=102)]

    results = find_only_grundriss(grundriss, matched_grundriss_ids={101})

    assert len(results) == 1
    assert results[0].anlage_ref_id == 102
    assert results[0].diff_type == DiffType.only_grundriss
    assert results[0].severity == Severity.warning


# attr_mismatch ------------------------------------------------------------


def test_attr_mismatch_bei_abweichendem_anlagentyp():
    s = _StubAnlage(id=1, anlagentyp="Lueftung")
    g = _StubAnlage(id=101, anlagentyp="Pumpe")

    result = find_attr_mismatch(s, g, score=95.0)

    assert result is not None
    assert result.diff_type == DiffType.attr_mismatch
    assert result.anlage_ref_id == 1
    assert result.partner_ref_id == 101
    assert result.details["schema_wert"] == "Lueftung"
    assert result.details["grundriss_wert"] == "Pumpe"


def test_attr_mismatch_none_bei_gleichem_typ():
    s = _StubAnlage(id=1, anlagentyp="Lueftung")
    g = _StubAnlage(id=101, anlagentyp="Lueftung")

    assert find_attr_mismatch(s, g, score=95.0) is None


def test_attr_mismatch_none_bei_fehlendem_wert():
    """Fehlende Information ist keine Abweichung."""
    s = _StubAnlage(id=1, anlagentyp="Lueftung")
    g = _StubAnlage(id=101, anlagentyp=None)

    assert find_attr_mismatch(s, g, score=95.0) is None


# room_mismatch ------------------------------------------------------------


def test_room_mismatch_bei_abweichendem_raum():
    s = _StubAnlage(id=1, room_code="E.801")
    g = _StubAnlage(id=101, room_code="EG.124")

    result = find_room_mismatch(s, g, score=90.0)

    assert result is not None
    assert result.diff_type == DiffType.room_mismatch
    assert result.details["schema_wert"] == "E.801"
    assert result.details["grundriss_wert"] == "EG.124"


def test_room_mismatch_none_bei_gleichem_raum():
    s = _StubAnlage(id=1, room_code="E.801")
    g = _StubAnlage(id=101, room_code="E.801")

    assert find_room_mismatch(s, g, score=90.0) is None


def test_room_mismatch_none_bei_fehlendem_raum():
    s = _StubAnlage(id=1, room_code=None)
    g = _StubAnlage(id=101, room_code="EG.124")

    assert find_room_mismatch(s, g, score=90.0) is None


# compute_diff (Integration der vier Typen) --------------------------------


def test_compute_diff_alle_vier_typen():
    schema = [
        _StubAnlage(id=1, anlagentyp="Lueftung", room_code="E.801"),  # gematcht
        _StubAnlage(id=2),  # only_schema
    ]
    grundriss = [
        _StubAnlage(id=101, anlagentyp="Pumpe", room_code="EG.124"),  # gematcht
        _StubAnlage(id=102),  # only_grundriss
    ]
    pairs = [_StubPair(schema_anlage_id=1, grundriss_anlage_id=101)]

    results = compute_diff(schema, grundriss, pairs)

    assert len(_by_type(results, DiffType.only_schema)) == 1
    assert len(_by_type(results, DiffType.only_grundriss)) == 1
    assert len(_by_type(results, DiffType.attr_mismatch)) == 1
    assert len(_by_type(results, DiffType.room_mismatch)) == 1


def test_compute_diff_ignoriert_rejected_matches():
    """Verworfene Matches gelten als nicht gematcht."""
    schema = [_StubAnlage(id=1)]
    grundriss = [_StubAnlage(id=101)]
    pairs = [_StubPair(schema_anlage_id=1, grundriss_anlage_id=101, status="rejected")]

    results = compute_diff(schema, grundriss, pairs)

    assert len(_by_type(results, DiffType.only_schema)) == 1
    assert len(_by_type(results, DiffType.only_grundriss)) == 1


def test_compute_diff_waehlt_bestes_paar_bei_1_zu_n():
    """Bei mehreren Kandidaten zaehlt nur das Paar mit dem hoechsten Score."""
    schema = [_StubAnlage(id=1, room_code="E.801")]
    grundriss = [
        _StubAnlage(id=101, room_code="E.801"),  # bester Score, kein Mismatch
        _StubAnlage(id=102, room_code="EG.999"),  # schlechter, wuerde Mismatch geben
    ]
    pairs = [
        _StubPair(schema_anlage_id=1, grundriss_anlage_id=101, score=98.0),
        _StubPair(schema_anlage_id=1, grundriss_anlage_id=102, score=86.0),
    ]

    results = compute_diff(schema, grundriss, pairs)

    # Bestes Paar (101) hat gleichen Raum -> kein room_mismatch
    assert _by_type(results, DiffType.room_mismatch) == []
    # 102 verliert die Auswahl und bleibt damit unzugeordnet
    only_g = _by_type(results, DiffType.only_grundriss)
    assert [r.anlage_ref_id for r in only_g] == [102]


def test_compute_diff_tiebreak_waehlt_kleinere_grundriss_id():
    """Bei gleichem Score entscheidet die kleinere Grundriss-Id (deterministisch)."""
    schema = [_StubAnlage(id=1, room_code="E.801")]
    grundriss = [
        _StubAnlage(id=101, room_code="EG.111"),  # gewinnt (kleinere Id)
        _StubAnlage(id=102, room_code="EG.222"),
    ]
    # Reihenfolge bewusst umgekehrt: die kleinere Id kommt zuletzt
    pairs = [
        _StubPair(schema_anlage_id=1, grundriss_anlage_id=102, score=90.0),
        _StubPair(schema_anlage_id=1, grundriss_anlage_id=101, score=90.0),
    ]

    results = compute_diff(schema, grundriss, pairs)

    # Gewaehlt wurde 101 -> room_mismatch verweist auf dessen Raum
    mismatches = _by_type(results, DiffType.room_mismatch)
    assert len(mismatches) == 1
    assert mismatches[0].partner_ref_id == 101
    assert mismatches[0].details["grundriss_wert"] == "EG.111"
    # 102 hat die Auswahl verloren und bleibt unzugeordnet
    only_g = _by_type(results, DiffType.only_grundriss)
    assert [r.anlage_ref_id for r in only_g] == [102]


def test_compute_diff_leere_eingaben():
    assert compute_diff([], [], []) == []
