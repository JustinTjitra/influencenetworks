"""Deterministic normalisation of Indonesian personal names as printed in filings.

No fuzzy, phonetic or silent matching: two printed names are the same only when
their normalised forms are identical (see CLAUDE.md, hard rule 3).
"""

from __future__ import annotations

import re
import unicodedata

# Honorifics and academic or professional degrees removed from names.
# Entries are upper-case with no dots, spaces or parentheses ("S.E." is "SE",
# "Dr. (H.C.)" is "DR" and "HC").  To extend: add the upper-case dotless form
# here; matching is case-insensitive and ignores dots.  Beware of entries that
# are also real name tokens (for example "MA", "CA", "R"): adding them means
# that token is dropped wherever it appears as a separate word.
TITLES: frozenset[str] = frozenset(
    {
        # honorifics
        "H", "HJ", "IR", "DR", "DRS", "DRA", "PROF", "TN", "NY", "KH", "RADEN", "R",
        # Indonesian degrees
        "SE", "SH", "ST", "SIP", "SKOM", "SSOS", "MM", "MH", "MA", "MKN", "MHUM",
        "MSI", "MT", "MMT", "SPD", "MPD", "MKOM", "SKM", "DRG", "DRH",
        # international degrees and designations
        "BA", "BBA", "MBA", "MSC", "PHD", "BSC", "LLM", "LLB", "AK", "CA", "CFA", "CPA",
        # honorary marker as in "Dr. (H.C.)"
        "HC",
    }
)

_STRIP_CHARS = ".,;:()[]{}\"“”"


def _clean(token: str) -> str:
    # Surrounding punctuation and inner dots go ("P.M." -> "PM"); hyphens and
    # apostrophes stay.
    return token.strip(_STRIP_CHARS).replace(".", "")


def _is_title(token: str) -> bool:
    joined = re.sub(r"[.()\[\]{}]", "", token).upper()
    if not joined:
        return False
    if joined in TITLES:
        return True
    # "Ir.H." style: every dot-separated piece is itself a title.
    pieces = [p for p in re.split(r"[.()\[\]{}]", token.upper()) if p]
    return len(pieces) > 1 and all(p in TITLES for p in pieces)


def normalise(name: str) -> str:
    """Return the comparable form of a printed name (upper case, titles removed).

    If every token is a title (for example "Ir"), the cleaned tokens are kept so
    that a whole-name token is never erased.
    """
    text = unicodedata.normalize("NFKC", name or "")
    raw = [t for t in re.split(r"[\s,]+", text.strip()) if t]
    kept: list[str] = []
    cleaned_all: list[str] = []
    for tok in raw:
        cleaned = _clean(tok)
        if not cleaned:
            continue
        cleaned_all.append(cleaned)
        if not _is_title(tok):
            kept.append(cleaned)
    result = kept if kept else cleaned_all
    return " ".join(result).upper()


def tokens(name: str) -> tuple[str, ...]:
    """The normalised name split on spaces."""
    norm = normalise(name)
    return tuple(norm.split(" ")) if norm else ()


def block_keys(name: str) -> set[str]:
    """Exact tokens of length 3 or more, used to choose which pairs to compare."""
    return {t for t in tokens(name) if len(t) >= 3}


def same_printed(a: str, b: str) -> bool:
    """True only when the normalised forms are identical (and non-empty)."""
    na, nb = normalise(a), normalise(b)
    return bool(na) and na == nb
