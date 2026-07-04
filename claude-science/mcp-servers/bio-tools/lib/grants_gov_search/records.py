"""Canonicalization of Grants.gov opportunity records.

Canonicalization rules (contract section 2; documented in README):
  * records sorted by (number, id) — pagination order is made irrelevant
  * JSON keys sorted, compact separators
  * no fields dropped or rewritten: the search2 hit record contains no
    volatile fields (no timestamps/request IDs); ``cfdaList`` order is
    preserved as stored upstream (byte-identical across query routes,
    verified at build).
"""
from __future__ import annotations

import json


def canonical_records(records: list[dict]) -> list[dict]:
    """Deterministically ordered copy of a record list."""
    return sorted(records, key=lambda r: (r.get("number", ""), r.get("id", "")))


def canonical_json(records: list[dict]) -> str:
    """Canonical serialization used for run-identity hashing and token counts."""
    return json.dumps(canonical_records(records), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
