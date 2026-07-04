"""Shared canonicalization used by the equivalence gate (bench/run_gate.py).

Rules (documented in README.md):
  1. Drop volatile metadata fields: _score (relevance score, request-dependent) and
     _version (document version counter) at any nesting level.
  2. Recursively sort dictionary keys.
  3. Treat the record collection per query term as unordered: sort records by
     (query, _id, full canonical JSON) before serializing.
  4. Serialize with compact separators and sort_keys=True; non-JSON scalars via str().
List element order *within* a field value (e.g. alias lists) is preserved as returned by
the API -- it is scientific content and is not re-sorted.
"""
from __future__ import annotations

import json

VOLATILE_FIELDS = ("_score", "_version")


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in sorted(obj.items()) if k not in VOLATILE_FIELDS}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def canonicalize_record(record: dict) -> dict:
    """Drop volatile fields and recursively key-sort a single record."""
    return _strip(record)


def canonicalize_records(records) -> bytes:
    """Canonical byte representation of an (unordered) collection of records."""
    canon = [canonicalize_record(r) for r in records]
    canon.sort(
        key=lambda r: (
            str(r.get("query", "")),
            str(r.get("_id", "")),
            json.dumps(r, sort_keys=True, default=str),
        )
    )
    return json.dumps(canon, sort_keys=True, separators=(",", ":"), default=str).encode()


def group_by_query(records) -> dict:
    """Group records by their `query` field (the input term that produced them)."""
    groups: dict[str, list] = {}
    for rec in records:
        groups.setdefault(str(rec.get("query", "")), []).append(rec)
    return groups
