"""Fuzzy-Matching zwischen Schema- und Grundriss-Anlagen via rapidfuzz."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from rapidfuzz import fuzz

DEFAULT_METHOD = "fuzzy_token_sort"


@dataclass(slots=True)
class MatchCandidate:
    """Ein einzelnes Fuzzy-Match-Resultat zwischen zwei Anlagen."""

    schema_id: int
    grundriss_id: int
    score: float
    method: str = DEFAULT_METHOD


@dataclass(slots=True)
class _AnlageRef:
    """Minimales DTO fuer den Matcher (entkoppelt von SQLAlchemy)."""

    id: int
    label_normalized: str


def to_refs(anlagen: Iterable) -> list[_AnlageRef]:
    """Konvertiert beliebige Anlage-aehnliche Objekte zu _AnlageRefs."""
    return [_AnlageRef(id=a.id, label_normalized=a.label_normalized) for a in anlagen]


def match_anlagen(
    schema: Sequence,
    grundriss: Sequence,
    threshold: int,
) -> list[MatchCandidate]:
    """Liefert alle Match-Kandidaten ueber Threshold (1:n).

    Fuer jede Schema-Anlage werden alle Grundriss-Anlagen zurueckgegeben,
    deren ``token_sort_ratio`` >= ``threshold`` liegt. Reine Funktion,
    keine DB-Bindung — Aufrufer uebergeben Anlage-Objekte (oder _AnlageRef).
    """
    if not schema or not grundriss:
        return []

    schema_refs = to_refs(schema)
    grundriss_refs = to_refs(grundriss)

    # Score-Cutoff entlastet rapidfuzz: liefert 0 zurueck wenn unter Threshold
    cutoff = float(threshold)
    candidates: list[MatchCandidate] = []
    for s_ref in schema_refs:
        for g_ref in grundriss_refs:
            score = fuzz.token_sort_ratio(
                s_ref.label_normalized,
                g_ref.label_normalized,
                score_cutoff=cutoff,
            )
            if score < cutoff:
                continue
            candidates.append(
                MatchCandidate(
                    schema_id=s_ref.id,
                    grundriss_id=g_ref.id,
                    score=float(score),
                )
            )
    return candidates
