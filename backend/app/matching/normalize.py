"""Label-Normalisierung fuer den Anlagen-Abgleich.

Im MVP einfach: trim, lower, Whitespace kollabieren, Trennzeichen
zwischen Praefix und Nummer entfernen. Synonym-Map wird in Phase 6 ergaenzt.
"""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
# Trennzeichen zwischen Buchstaben und Ziffern (L 01, RLT-04 -> L01, RLT04)
_INNER_SEP = re.compile(r"(?<=[A-Za-z])[\s\-_\.]+(?=\d)")


def normalize_label(raw: str, synonyms: dict[str, str] | None = None) -> str:
    """Liefert eine normalisierte Form des Labels fuer Vergleich/Matching."""
    if not raw:
        return ""
    text = raw.strip().lower()
    text = _WS.sub(" ", text)
    text = _INNER_SEP.sub("", text)
    if synonyms:
        for src, dst in synonyms.items():
            text = text.replace(src.lower(), dst.lower())
    return text
