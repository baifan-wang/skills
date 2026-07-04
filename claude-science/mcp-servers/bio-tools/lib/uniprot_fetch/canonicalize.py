"""Shared canonicalization used by the equivalence gate (legacy reference vs modern output).

Applied canonicalizations (all permitted by the contract; nothing scientific is altered):

1. Line endings normalized to ``\\n``.
2. Trailing whitespace stripped from each line.
3. Blank lines dropped (FASTA) / trailing blank lines dropped (flat-file); exactly one
   trailing newline at the end of the record.
4. FASTA only: the sequence is re-wrapped at 60 columns so the comparison is independent
   of line-wrap width (UniProt uses 60 columns on both endpoints, so this is a no-op in
   practice, but it makes the gate robust).

NOT altered: FASTA headers, sequences, and every flat-file line including ``DT`` (entry
version / release dates), feature tables, and cross-references — these are compared verbatim.
"""
from __future__ import annotations


def _norm_lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def canonicalize_fasta(text: str) -> bytes:
    """Canonical byte representation of a (single- or multi-record) FASTA string."""
    out: list[str] = []
    seq: list[str] = []

    def flush() -> None:
        if seq:
            joined = "".join(seq)
            for i in range(0, len(joined), 60):
                out.append(joined[i : i + 60])
            seq.clear()

    for ln in _norm_lines(text):
        if not ln:
            continue
        if ln.startswith(">"):
            flush()
            out.append(ln)
        else:
            seq.append(ln)
    flush()
    return ("\n".join(out) + "\n").encode("utf-8")


def canonicalize_flatfile(text: str) -> bytes:
    """Canonical byte representation of a UniProtKB flat-file entry."""
    lines = _norm_lines(text)
    while lines and not lines[-1]:
        lines.pop()
    return ("\n".join(lines) + "\n").encode("utf-8")
