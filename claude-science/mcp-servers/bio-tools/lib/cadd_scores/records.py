"""Normalization of the CADD API's two response shapes into one record form.

Score record (the tool's single output shape):

    {"chrom": "17", "pos": 7676154, "ref": "G", "alt": "C",
     "raw_score": "0.612327", "phred": "12.91"}

``pos`` is an int; ``raw_score`` and ``phred`` are kept as the API's exact
decimal strings (never float-round-tripped) so equivalence gating is
byte-exact. Callers wanting numbers should float() them.
"""
from __future__ import annotations

import json

RANGE_HEADER = ["Chrom", "Pos", "Ref", "Alt", "RawScore", "PHRED"]


class MalformedResponse(ValueError):
    """The API payload did not match either documented shape."""


def _record(chrom, pos, ref, alt, raw_score, phred) -> dict:
    return {
        "chrom": str(chrom),
        "pos": int(pos),
        "ref": str(ref),
        "alt": str(alt),
        "raw_score": str(raw_score),
        "phred": str(phred),
    }


def normalize_position_response(payload) -> list[dict]:
    """Position query shape: JSON list of dicts with capitalized keys."""
    if not isinstance(payload, list):
        raise MalformedResponse(f"expected list, got {type(payload).__name__}")
    out = []
    for row in payload:
        if not isinstance(row, dict):
            raise MalformedResponse(f"expected dict rows, got {type(row).__name__}")
        try:
            out.append(_record(row["Chrom"], row["Pos"], row["Ref"], row["Alt"],
                               row["RawScore"], row["PHRED"]))
        except KeyError as exc:
            raise MalformedResponse(f"missing key {exc} in position row") from exc
    return sort_records(out)


def normalize_range_response(payload) -> list[dict]:
    """Range query shape: JSON list-of-lists, first row is the header."""
    if not isinstance(payload, list):
        raise MalformedResponse(f"expected list, got {type(payload).__name__}")
    if not payload:
        return []
    header = payload[0]
    if header != RANGE_HEADER:
        raise MalformedResponse(f"unexpected range header: {header!r}")
    out = []
    for row in payload[1:]:
        if not isinstance(row, list) or len(row) != len(RANGE_HEADER):
            raise MalformedResponse(f"bad range row: {row!r}")
        chrom, pos, ref, alt, raw_score, phred = row
        out.append(_record(chrom, pos, ref, alt, raw_score, phred))
    return sort_records(out)


def sort_records(records: list[dict]) -> list[dict]:
    """Stable canonical order: (chrom, pos, ref, alt)."""
    return sorted(records, key=lambda r: (r["chrom"], r["pos"], r["ref"], r["alt"]))


def canonicalize(obj) -> bytes:
    """Canonical JSON bytes: sorted keys, compact separators, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
