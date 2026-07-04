"""Canonicalization and deterministic ordering helpers.

Shared by the library, the accuracy gate, and the benchmark so that every
byte-equality check uses exactly one rule set.

Rules (documented in README; per docs/CONTRACT.md only ordering/serialization
is normalized -- no scientific content is dropped or rewritten):

* canonical JSON: sorted keys, compact separators, UTF-8 bytes;
* similarity result lists are sorted by (-similarity, molecule_chembl_id)
  client-side, because the /similarity route rejects ``order_by`` (HTTP 400);
* substructure / indication / warning lists are sorted by their resource id
  key (``molecule_chembl_id`` / ``drugind_id`` / ``warning_id``);
* warning summaries de-duplicate (type, class, country, year) tuples and sort.
"""

from __future__ import annotations

import json
from typing import Any


def canonicalize(obj: Any) -> bytes:
    """Canonical JSON bytes: sorted keys, compact separators, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sort_similarity_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic similarity ordering: descending similarity, then ChEMBL ID.

    The API's own ordering on this route is not contractual and ``order_by``
    is rejected upstream, so determinism is enforced here.
    """
    return sorted(
        records,
        key=lambda r: (-float(r.get("similarity") or 0.0), r.get("molecule_chembl_id") or ""),
    )


def sort_by_key(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """Sort records by a scalar resource key (None sorts first, stable)."""
    return sorted(records, key=lambda r: (r.get(key) is not None, r.get(key)))


def summarize_warnings(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """De-duplicated, sorted (warning_type, warning_class, warning_country, warning_year) summary."""
    seen = {
        (
            w.get("warning_type"),
            w.get("warning_class"),
            w.get("warning_country"),
            w.get("warning_year"),
        )
        for w in warnings
    }
    return [
        {
            "warning_type": t,
            "warning_class": c,
            "warning_country": co,
            "warning_year": y,
        }
        for (t, c, co, y) in sorted(seen, key=lambda x: tuple("" if v is None else str(v) for v in x))
    ]
