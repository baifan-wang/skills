"""Canonicalization shared by the equivalence gate (bench/run_gate.py).

Rules (whitespace-only; documented in README):
  1. Normalize line endings to '\\n'.
  2. Strip trailing whitespace from every line.
  3. Drop trailing blank lines; the record ends with a single trailing newline.

No scientific content (field values, sequences, identifiers, the '///'
terminator) is altered, dropped, or reordered.
"""

from __future__ import annotations


def canonicalize(text: str) -> bytes:
    """Canonical byte representation of a KEGG flat-file record for comparison."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return ("\n".join(lines) + "\n").encode("utf-8")
