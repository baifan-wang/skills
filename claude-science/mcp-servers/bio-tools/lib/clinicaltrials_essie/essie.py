"""Essie expression builders for the ClinicalTrials.gov v2 API.

AREA names are study-record *piece names* (verified against
GET /api/v2/studies/metadata, API 2.0.5, 454 pieces) — not only the 19
search-area names from /studies/search-areas. Both vocabularies are accepted
by the Essie engine in `filter.advanced` and `query.term`.

Verified behaviors (live, 2026-06-08, API 2.0.5):
- `AREA[OverallOfficialName]"John Smith"` (quoted) matches the phrase within a
  single official's name; unquoted `John Smith` matches tokens across
  *different* officials of the same study (e.g. "John S Bynon" + "Blair
  Smith") — quoting is mandatory for name searches.
- `SEARCH[Location](...)` groups location sub-areas so city/country/status
  constraints must hold at the SAME site.
- `RANGE[MIN, x]` / `RANGE[x, MAX]` open bounds; dates as YYYY-MM-DD; ages as
  ISO-8601-ish strings ("18 years").
- The same expression yields identical counts via `filter.advanced` and
  `query.term` (used by the gate's two-formulation check).
"""

from __future__ import annotations

__all__ = [
    "quote_phrase", "area_phrase", "area_term", "area_range",
    "search_location", "and_join", "or_join",
]


def quote_phrase(text: str) -> str:
    """Quote a phrase for Essie, escaping embedded double quotes."""
    return '"' + text.replace('"', '\\"') + '"'


def area_phrase(area: str, phrase: str) -> str:
    """AREA[<area>]"<phrase>" — quoted phrase match within one field value."""
    return f"AREA[{area}]{quote_phrase(phrase)}"


def area_term(area: str, term: str) -> str:
    """AREA[<area>]<term> — raw (unquoted) Essie term, e.g. enums: PHASE3, FEMALE, y."""
    return f"AREA[{area}]{term}"


def area_range(area: str, lo: str | None, hi: str | None) -> str:
    """AREA[<area>]RANGE[lo, hi] with MIN/MAX for open bounds."""
    return f"AREA[{area}]RANGE[{lo or 'MIN'}, {hi or 'MAX'}]"


def search_location(*exprs: str) -> str:
    """SEARCH[Location](...) — constrain sub-expressions to the same study site."""
    return f"SEARCH[Location]({' AND '.join(exprs)})"


def and_join(*exprs: str | None) -> str:
    """AND-join non-empty expressions, parenthesizing OR-bearing terms."""
    kept = [e for e in exprs if e]
    if not kept:
        raise ValueError("no expressions to join")
    return " AND ".join(_paren_if_or(e) for e in kept)


def or_join(*exprs: str | None) -> str:
    """OR-join non-empty expressions."""
    kept = [e for e in exprs if e]
    if not kept:
        raise ValueError("no expressions to join")
    if len(kept) == 1:
        return kept[0]
    return "(" + " OR ".join(kept) + ")"


def _paren_if_or(expr: str) -> str:
    """Parenthesize an expression containing a top-level OR (defensive)."""
    if " OR " in expr and not (expr.startswith("(") and expr.endswith(")")):
        return f"({expr})"
    return expr
