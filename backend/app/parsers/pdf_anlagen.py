"""PDF-Parser zur Extraktion von Anlagen-Bezeichnungen samt Positionen.

Nutzt PyMuPDF (fitz). Liefert eine Liste von ``ExtractedAnlage``-DTOs,
die der Extraction-Service in die Datenbank schreibt.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import fitz

logger = logging.getLogger(__name__)


# --- Public DTO -----------------------------------------------------------


@dataclass(slots=True)
class ExtractedAnlage:
    """Roher Treffer aus dem PDF, vor DB-Insertion."""

    label_raw: str
    anlagentyp: str | None
    page: int
    x: float
    y: float
    room_code: str | None = None
    attributes: dict = field(default_factory=dict)


# --- Regex-Definitionen ---------------------------------------------------

# Kurzbezeichnungen wie "L01", "RLT-04", "P 12", "WRG-2a"
# Typische HLK-Praefixe (erweiterbar pro Projekt ueber synonyms_json)
_HLK_PREFIXES = (
    "RLT", "LTG", "WRG", "VENT", "ABL", "ZUL", "FOL",
    "WT", "WE", "WP", "KM", "KA",
    "P", "V", "VV", "WW", "KK", "L",
)

# Pattern: PREFIX (optional Trenner) DIGITS (optional Suffix-Buchstabe)
# Word-Boundary verhindert false-positives ("KKL01" matched nicht "K" + "KL01")
_PATTERN_SHORTCODE = re.compile(
    r"\b(?P<prefix>" + "|".join(_HLK_PREFIXES) + r")"
    r"(?P<sep>[\s\-_\.]?)"
    r"(?P<num>\d{1,3})"
    r"(?P<suffix>[a-zA-Z])?\b"
)

# Volltext-Bezeichnungen (Wortlisten, die direkt als Anlagentyp dienen)
_VOLLTEXT_BEGRIFFE: dict[str, str] = {
    # Begriff (lowercase) -> kanonischer Anlagentyp
    "lueftungsgeraet": "Lueftungsgeraet",
    "lüftungsgerät": "Lueftungsgeraet",
    "rlt-anlage": "RLT-Anlage",
    "rlt anlage": "RLT-Anlage",
    "pumpe": "Pumpe",
    "ventilator": "Ventilator",
    "waermepumpe": "Waermepumpe",
    "wärmepumpe": "Waermepumpe",
    "waermeuebertrager": "Waermeuebertrager",
    "wärmeübertrager": "Waermeuebertrager",
    "kaeltemaschine": "Kaeltemaschine",
    "kältemaschine": "Kaeltemaschine",
    "klimageraet": "Klimageraet",
    "klimagerät": "Klimageraet",
    "heizkessel": "Heizkessel",
    "verteiler": "Verteiler",
}

# Map Prefix -> Anlagentyp (fuer Shortcode-Klassifikation)
_PREFIX_TO_TYP: dict[str, str] = {
    "RLT": "RLT-Anlage",
    "LTG": "Leitung",
    "WRG": "Waermerueckgewinnung",
    "VENT": "Ventilator",
    "ABL": "Abluft",
    "ZUL": "Zuluft",
    "FOL": "Fortluft",
    "WT": "Waermeuebertrager",
    "WE": "Waermeerzeuger",
    "WP": "Waermepumpe",
    "KM": "Kaeltemaschine",
    "KA": "Klimaanlage",
    "P": "Pumpe",
    "V": "Ventilator",
    "VV": "Vorlaufventil",
    "WW": "Warmwasser",
    "KK": "Kaeltekreis",
    "L": "Lueftungsgeraet",
}

# Standard-Raumcodes, falls Projekt keine eigenen Patterns mitbringt
_DEFAULT_ROOM_PATTERNS: tuple[str, ...] = (
    r"\b[EU]G\.?\d{3}[a-z]?\b",       # E.801, EG.124, UG201
    r"\b[EU]\.\d{3}[a-z]?\b",         # E.801
    r"\bR[\-\s]?\d{3,4}\b",           # R-205, R 1024
    r"\b\d\.\d{2,3}[a-z]?\b",         # 1.024, 2.105a
)


# --- Hilfsklassen ---------------------------------------------------------


@dataclass(slots=True)
class _RoomLocation:
    code: str
    page: int
    x: float
    y: float


# --- Hauptfunktion --------------------------------------------------------


def extract_anlagen(
    pdf_path: Path,
    room_patterns: Iterable[str] | None = None,
) -> list[ExtractedAnlage]:
    """Extrahiert alle Anlagen aus einem PDF.

    ``room_patterns`` kann ueber das Projekt konfiguriert werden;
    fehlt es, werden die Standard-Patterns verwendet.
    """
    room_regexes = [
        re.compile(p) for p in (room_patterns or _DEFAULT_ROOM_PATTERNS)
    ]

    anlagen: list[ExtractedAnlage] = []
    rooms: list[_RoomLocation] = []

    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            page_anlagen, page_rooms = _process_page(
                page, page_index, room_regexes
            )
            anlagen.extend(page_anlagen)
            rooms.extend(page_rooms)

    _assign_rooms(anlagen, rooms)
    logger.info(
        "extract_anlagen: %d Anlagen, %d Raeume aus %s",
        len(anlagen),
        len(rooms),
        pdf_path.name,
    )
    return anlagen


# --- Per-Seite-Verarbeitung -----------------------------------------------


def _process_page(
    page: fitz.Page,
    page_index: int,
    room_regexes: list[re.Pattern[str]],
) -> tuple[list[ExtractedAnlage], list[_RoomLocation]]:
    """Verarbeitet eine PDF-Seite und liefert Anlagen + Raum-Locations."""
    anlagen: list[ExtractedAnlage] = []
    rooms: list[_RoomLocation] = []
    # Dedup nach normalisiertem Label pro Seite (z.B. "Pumpe P05" und "P05"
    # sollen nicht doppelt erfasst werden)
    seen_keys: set[str] = set()

    # get_text("words") liefert (x0, y0, x1, y1, "wort", block, line, word_no)
    words = page.get_text("words")

    # 1) Volltext-Anlagen zuerst: sie erfassen "Lueftungsgeraet LG-04"
    #    inklusive nachfolgendem Code, und der Code wird dadurch reserviert
    full_text = page.get_text("text")
    for hit_label, hit_typ, start in _find_volltext_anlagen(full_text):
        pos = _approx_position_for_text(page, hit_label)
        if pos is None:
            continue
        cx, cy = pos
        normalized_inner = _extract_inner_code(hit_label)
        key = normalized_inner or hit_label.lower()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        anlagen.append(
            ExtractedAnlage(
                label_raw=hit_label,
                anlagentyp=hit_typ,
                page=page_index,
                x=cx,
                y=cy,
                attributes={"match": "volltext", "normalized": normalized_inner or ""},
            )
        )

    # 2) Raum-Codes ueber Einzel- und Paar-Tokens sammeln. So wird auch
    #    "R 1024" als Paar-Token erkannt.
    pair_tokens = _iter_word_and_pair_tokens(words)
    for token_text, x0, y0, x1, y1 in pair_tokens:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for rx in room_regexes:
            m = rx.search(token_text)
            if m:
                rooms.append(_RoomLocation(m.group(0), page_index, cx, cy))
                break

    # 3) Shortcode-Anlagen: ueber Einzel-Wort UND ueber Paare aufeinanderfolgender
    #    Worte ("P" + "03" -> "P03"). Erkennt sowohl "P03" als auch "P 03".
    for token_text, x0, y0, x1, y1 in pair_tokens:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

        m = _PATTERN_SHORTCODE.fullmatch(token_text)
        if not m:
            continue

        prefix = m.group("prefix").upper()
        num = m.group("num")
        suffix = (m.group("suffix") or "").lower()
        normalized = f"{prefix.lower()}{num}{suffix}"
        if normalized in seen_keys:
            continue
        seen_keys.add(normalized)

        anlagen.append(
            ExtractedAnlage(
                label_raw=token_text,
                anlagentyp=_PREFIX_TO_TYP.get(prefix),
                page=page_index,
                x=cx,
                y=cy,
                attributes={"match": "shortcode", "normalized": normalized},
            )
        )

    return anlagen, rooms


def _iter_word_and_pair_tokens(
    words: list[tuple],
) -> list[tuple[str, float, float, float, float]]:
    """Liefert sowohl Einzelworte als auch Paare nebeneinanderliegender Worte.

    Worte gelten als Paar, wenn sie auf derselben Zeile (gleicher block/line)
    liegen. Damit wird "P" + "03" zu "P03" erkannt.
    """
    tokens: list[tuple[str, float, float, float, float]] = []
    for entry in words:
        x0, y0, x1, y1, word, *_rest = entry
        tokens.append((word, x0, y0, x1, y1))

    # Paare: beide Worte auf gleicher block/line
    for i in range(len(words) - 1):
        a, b = words[i], words[i + 1]
        a_block, a_line = a[5], a[6]
        b_block, b_line = b[5], b[6]
        if a_block != b_block or a_line != b_line:
            continue
        # Konkateniert ohne Leerzeichen — Regex erlaubt internen Trenner ohnehin
        combined = a[4] + b[4]
        tokens.append(
            (
                combined,
                min(a[0], b[0]),
                min(a[1], b[1]),
                max(a[2], b[2]),
                max(a[3], b[3]),
            )
        )
    return tokens


def _extract_inner_code(label: str) -> str:
    """Extrahiert den normalisierten Shortcode aus einem Volltext-Label.

    "Lueftungsgeraet LG-04" -> "lg04". Liefert "" wenn kein Code enthalten.
    """
    m = _PATTERN_SHORTCODE.search(label)
    if not m:
        return ""
    return f"{m.group('prefix').lower()}{m.group('num')}{(m.group('suffix') or '').lower()}"


@lru_cache(maxsize=1)
def _compiled_volltext_patterns() -> tuple[tuple[re.Pattern[str], str], ...]:
    """Compiled Pattern pro Volltext-Begriff mit linker und rechter Boundary.

    Links: Wortanfang oder Nicht-Buchstabe (verhindert Matches mitten in
    Komposita wie "Lueftungsgeraetekompressor"). Rechts: Nicht-Buchstabe
    (Whitespace, Bindestrich, Satzzeichen, EOF).
    """
    patterns: list[tuple[re.Pattern[str], str]] = []
    for begriff, typ in _VOLLTEXT_BEGRIFFE.items():
        regex = re.compile(
            r"(?:^|(?<=[^A-Za-zÄÖÜäöüß]))"
            + re.escape(begriff)
            + r"(?=[^A-Za-zÄÖÜäöüß]|$)",
            flags=re.IGNORECASE,
        )
        patterns.append((regex, typ))
    return tuple(patterns)


_CODE_TAIL = re.compile(r"\s+([A-Z]{1,4}[\s\-]?\d{1,3}[a-z]?)")


def _find_volltext_anlagen(text: str) -> list[tuple[str, str, int]]:
    """Findet Volltext-Anlagen-Begriffe und liefert (label, typ, start_offset).

    Boundary-Check verhindert Substring-Matches innerhalb deutscher Komposita.
    """
    hits: list[tuple[str, str, int]] = []
    for regex, typ in _compiled_volltext_patterns():
        for match in regex.finditer(text):
            idx = match.start()
            end = match.end()
            original = text[idx:end]
            tail = text[end : end + 20]
            code_match = _CODE_TAIL.match(tail)
            label = original + (code_match.group(0) if code_match else "")
            hits.append((label.strip(), typ, idx))
    return hits


def _approx_position_for_text(
    page: fitz.Page, label: str
) -> tuple[float, float] | None:
    """Sucht die Bounding-Box des Labels auf der Seite (erstes Vorkommen)."""
    # search_for arbeitet case-sensitive auf raw Text; wir nehmen das erste Wort
    first_word = label.split()[0] if label.split() else label
    rects = page.search_for(first_word, quads=False)
    if not rects:
        return None
    r = rects[0]
    return ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)


# --- Raumzuordnung --------------------------------------------------------


def _assign_rooms(
    anlagen: list[ExtractedAnlage], rooms: list[_RoomLocation]
) -> None:
    """Weist jeder Anlage den naechstgelegenen Raum derselben Seite zu."""
    rooms_by_page: dict[int, list[_RoomLocation]] = {}
    for r in rooms:
        rooms_by_page.setdefault(r.page, []).append(r)

    for anl in anlagen:
        candidates = rooms_by_page.get(anl.page)
        if not candidates:
            continue
        anl.room_code = _nearest_room(anl, candidates).code


def _nearest_room(
    anl: ExtractedAnlage, rooms: list[_RoomLocation]
) -> _RoomLocation:
    return min(
        rooms,
        key=lambda r: math.hypot(r.x - anl.x, r.y - anl.y),
    )
