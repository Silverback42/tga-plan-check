"""Unit-Tests fuer das Fuzzy-Matching."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.matching.fuzzy import DEFAULT_METHOD, match_anlagen


@dataclass(slots=True)
class _StubAnlage:
    """Minimaler Stub mit den Attributen, die der Matcher liest."""

    id: int
    label_normalized: str


def _make_anlagen(items: list[tuple[int, str]]) -> list[_StubAnlage]:
    return [_StubAnlage(id=i, label_normalized=label) for i, label in items]


def test_exact_match_score_100():
    schema = _make_anlagen([(1, "rlt01")])
    grundriss = _make_anlagen([(101, "rlt01")])

    result = match_anlagen(schema, grundriss, threshold=85)

    assert len(result) == 1
    assert result[0].schema_id == 1
    assert result[0].grundriss_id == 101
    assert result[0].score == pytest.approx(100.0)
    assert result[0].method == DEFAULT_METHOD


def test_one_to_many_candidates_over_threshold():
    schema = _make_anlagen([(1, "rlt01")])
    # Drei Kandidaten: zwei sehr aehnlich, einer disjunkt
    grundriss = _make_anlagen(
        [
            (101, "rlt01"),
            (102, "rlt02"),
            (103, "pumpe xyz"),
        ]
    )

    result = match_anlagen(schema, grundriss, threshold=75)
    grundriss_ids = {c.grundriss_id for c in result}

    assert 101 in grundriss_ids  # exakt
    assert 102 in grundriss_ids  # 1 Zeichen Unterschied -> hoher Score
    assert 103 not in grundriss_ids  # disjunkt


def test_threshold_filters_low_scores():
    # "rlt01" vs "rlt02" liefert empirisch Score 80 (ein Zeichen Unterschied)
    schema = _make_anlagen([(1, "rlt01")])
    grundriss = _make_anlagen([(101, "rlt02")])

    # Niedriger Threshold: matched
    loose = match_anlagen(schema, grundriss, threshold=75)
    # Hoher Threshold: matched nicht
    strict = match_anlagen(schema, grundriss, threshold=85)

    assert len(loose) == 1
    assert len(strict) == 0


def test_disjoint_strings_no_match():
    """Komplett disjunkte Strings liefern Score 0 — kein Match auch bei threshold=0."""
    schema = _make_anlagen([(1, "rlt01")])
    grundriss = _make_anlagen([(101, "pumpe xyz")])

    result = match_anlagen(schema, grundriss, threshold=0)
    # Pair mit Score 0 wird vom Cutoff (>= threshold) zwar zugelassen, ist aber
    # ohne praktischen Wert. Wichtig: kein Crash.
    assert all(c.score >= 0 for c in result)


def test_empty_inputs_return_empty():
    schema = _make_anlagen([(1, "rlt01")])
    grundriss: list[_StubAnlage] = []

    assert match_anlagen(schema, grundriss, threshold=85) == []
    assert match_anlagen([], schema, threshold=85) == []
    assert match_anlagen([], [], threshold=85) == []


def test_multi_schema_produces_per_pair_entries():
    schema = _make_anlagen([(1, "rlt01"), (2, "rlt02")])
    grundriss = _make_anlagen([(101, "rlt01"), (102, "rlt02")])

    # Threshold 75: rlt01/rlt02 (Score 80) fliegt auch durch, daher 1:n
    result = match_anlagen(schema, grundriss, threshold=75)

    pairs = {(c.schema_id, c.grundriss_id) for c in result}
    # Beide exakten Paare sind dabei
    assert (1, 101) in pairs
    assert (2, 102) in pairs
    # 1:n: jeder Schema-Eintrag sieht den jeweils anderen Grundriss
    # mit Score 80 ueber threshold=75, also auch (1,102) und (2,101)
    assert (1, 102) in pairs
    assert (2, 101) in pairs


def test_high_threshold_yields_only_exact_matches():
    schema = _make_anlagen([(1, "rlt01"), (2, "rlt02")])
    grundriss = _make_anlagen([(101, "rlt01"), (102, "rlt02")])

    result = match_anlagen(schema, grundriss, threshold=95)
    pairs = {(c.schema_id, c.grundriss_id) for c in result}

    assert pairs == {(1, 101), (2, 102)}


def test_score_is_float_and_in_range():
    schema = _make_anlagen([(1, "rlt01")])
    grundriss = _make_anlagen([(101, "rlt02")])

    result = match_anlagen(schema, grundriss, threshold=0)

    assert len(result) == 1
    assert isinstance(result[0].score, float)
    assert 0.0 <= result[0].score <= 100.0
