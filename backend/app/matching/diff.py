"""Diff-Logik zwischen Schema- und Grundriss-Anlagen (4 Diff-Typen).

Reine Funktionen ohne DB-Bindung: der Aufrufer uebergibt Anlage-aehnliche
Objekte und MatchPair-aehnliche Objekte, zurueck kommen ``DiffResult``-DTOs,
die der Service in ``DiffEntry``-Rows uebersetzt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from app.models import DiffType, Severity

# Nur diese Match-Status gelten als "gematcht"; rejected wird ignoriert,
# damit verworfene Vorschlaege wieder als Fehlstelle auftauchen.
ACTIVE_MATCH_STATES = frozenset({"auto", "confirmed", "manual"})


@dataclass(slots=True)
class DiffResult:
    """Ein erkannter Unterschied, noch ohne DB-Identitaet."""

    diff_type: DiffType
    severity: Severity
    anlage_ref_id: int | None = None
    partner_ref_id: int | None = None
    details: dict = field(default_factory=dict)


def _is_active(pair) -> bool:
    """Prueft, ob ein MatchPair als gueltige Zuordnung zaehlt."""
    status = getattr(pair.status, "value", pair.status)
    return status in ACTIVE_MATCH_STATES


def _best_pairs_by_schema(pairs: Sequence) -> dict[int, object]:
    """Reduziert 1:n-Matches auf das beste Paar je Schema-Anlage.

    Sortierschluessel: hoechster Score, bei Gleichstand die kleinere
    Grundriss-Id — damit ist das Ergebnis deterministisch.
    """
    best: dict[int, object] = {}
    for pair in pairs:
        current = best.get(pair.schema_anlage_id)
        if current is None or (pair.score, -pair.grundriss_anlage_id) > (
            current.score,
            -current.grundriss_anlage_id,
        ):
            best[pair.schema_anlage_id] = pair
    return best


def find_only_schema(
    schema: Iterable, matched_schema_ids: set[int]
) -> list[DiffResult]:
    """Schema-Anlagen ohne Gegenstueck im Grundriss."""
    return [
        DiffResult(
            diff_type=DiffType.only_schema,
            severity=Severity.error,
            anlage_ref_id=anlage.id,
            details={
                "label_raw": anlage.label_raw,
                "gewerk": getattr(anlage.gewerk, "value", anlage.gewerk),
                "room_code": anlage.room_code,
            },
        )
        for anlage in schema
        if anlage.id not in matched_schema_ids
    ]


def find_only_grundriss(
    grundriss: Iterable, matched_grundriss_ids: set[int]
) -> list[DiffResult]:
    """Grundriss-Anlagen ohne Gegenstueck im Schema."""
    return [
        DiffResult(
            diff_type=DiffType.only_grundriss,
            severity=Severity.warning,
            anlage_ref_id=anlage.id,
            details={
                "label_raw": anlage.label_raw,
                "gewerk": getattr(anlage.gewerk, "value", anlage.gewerk),
                "room_code": anlage.room_code,
            },
        )
        for anlage in grundriss
        if anlage.id not in matched_grundriss_ids
    ]


def find_attr_mismatch(schema_anlage, grundriss_anlage, score: float) -> DiffResult | None:
    """Gematchtes Paar mit abweichendem Anlagentyp."""
    schema_typ = schema_anlage.anlagentyp
    grundriss_typ = grundriss_anlage.anlagentyp
    # Fehlende Werte sind keine Abweichung, sondern fehlende Information
    if not schema_typ or not grundriss_typ:
        return None
    if schema_typ == grundriss_typ:
        return None
    return DiffResult(
        diff_type=DiffType.attr_mismatch,
        severity=Severity.warning,
        anlage_ref_id=schema_anlage.id,
        partner_ref_id=grundriss_anlage.id,
        details={
            "attribut": "anlagentyp",
            "schema_wert": schema_typ,
            "grundriss_wert": grundriss_typ,
            "score": score,
        },
    )


def find_room_mismatch(schema_anlage, grundriss_anlage, score: float) -> DiffResult | None:
    """Gematchtes Paar mit abweichendem Raum-Code."""
    schema_room = schema_anlage.room_code
    grundriss_room = grundriss_anlage.room_code
    if not schema_room or not grundriss_room:
        return None
    if schema_room == grundriss_room:
        return None
    return DiffResult(
        diff_type=DiffType.room_mismatch,
        severity=Severity.warning,
        anlage_ref_id=schema_anlage.id,
        partner_ref_id=grundriss_anlage.id,
        details={
            "attribut": "room_code",
            "schema_wert": schema_room,
            "grundriss_wert": grundriss_room,
            "score": score,
        },
    )


def compute_diff(
    schema: Sequence,
    grundriss: Sequence,
    pairs: Sequence,
) -> list[DiffResult]:
    """Berechnet alle vier Diff-Typen fuer ein Projekt.

    ``pairs`` darf 1:n sein — pro Schema-Anlage wird das beste Paar gewaehlt.
    """
    active = [p for p in pairs if _is_active(p)]
    # Nur das je Schema-Anlage gewaehlte Paar gilt als Zuordnung. Eine
    # Grundriss-Anlage, die die Auswahl verliert, bleibt unzugeordnet und
    # muss weiterhin als only_grundriss auftauchen.
    selected = list(_best_pairs_by_schema(active).values())
    matched_schema_ids = {p.schema_anlage_id for p in selected}
    matched_grundriss_ids = {p.grundriss_anlage_id for p in selected}

    results: list[DiffResult] = []
    results.extend(find_only_schema(schema, matched_schema_ids))
    results.extend(find_only_grundriss(grundriss, matched_grundriss_ids))

    by_id = {a.id: a for a in list(schema) + list(grundriss)}
    for pair in selected:
        s_anlage = by_id.get(pair.schema_anlage_id)
        g_anlage = by_id.get(pair.grundriss_anlage_id)
        if s_anlage is None or g_anlage is None:
            continue
        for finder in (find_attr_mismatch, find_room_mismatch):
            hit = finder(s_anlage, g_anlage, pair.score)
            if hit is not None:
                results.append(hit)
    return results
