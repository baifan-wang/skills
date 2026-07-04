"""BindingDB retrieval methods over :class:`BindingDbClient`.

Rows are normalized to plain keys (the ``bdb.``-prefixed variants from the
compound route are stripped) and sorted deterministically. Caps live in the
tier-2 server; these methods return the complete row set plus the upstream
hit count where the API provides one.
"""

from __future__ import annotations

import re

from .client import BindingDbClient

_UNIPROT_RE = re.compile(
    r"^[OPQ][0-9][A-Z0-9]{3}[0-9]$|^[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}$",
    re.IGNORECASE)


class BindingDbAffinities:
    """High-level BindingDB affinity retrieval."""

    def __init__(self, client: BindingDbClient | None = None):
        self.client = client or BindingDbClient()

    def ligands_by_uniprot(self, uniprot: str, cutoff_nm: int) -> list[dict]:
        """All ligand affinity rows for one UniProt target with affinity
        value <= cutoff_nm (nM).

        The route returns every matching measurement (no upstream total
        field); the returned list IS the complete set.
        """
        uniprot = uniprot.strip().upper()
        if not _UNIPROT_RE.match(uniprot):
            raise ValueError(f"not a UniProt accession: {uniprot!r}")
        if not (1 <= cutoff_nm <= 10_000_000):
            raise ValueError("cutoff_nm must be in [1, 10000000]")
        root = self.client.get_json_root(
            "getLigandsByUniprots",
            {"uniprot": uniprot, "cutoff": int(cutoff_nm), "code": 0})
        rows = []
        for raw in root.get("affinities", []) or []:
            rows.append({
                "target_name": raw.get("query"),
                "monomer_id": _as_str(raw.get("monomerid")),
                "smiles": raw.get("smile"),
                "affinity_type": raw.get("affinity_type"),
                "affinity": _as_str(raw.get("affinity")),
                "pmid": _as_str(raw.get("pmid")) or None,
                "doi": raw.get("doi") or None,
            })
        rows.sort(key=lambda r: (r["affinity_type"] or "",
                                 _affinity_sort_key(r["affinity"]),
                                 r["monomer_id"] or ""))
        return rows

    def targets_by_compound(self, smiles: str, similarity: float) -> dict:
        """Targets/affinities for compounds 2D-similar to a query SMILES.

        Returns ``{hit, rows}`` — ``hit`` is the upstream's own hit count
        (``bdb.hit``), so callers can verify the row set is complete.
        """
        if not smiles or not smiles.strip():
            raise ValueError("smiles must be non-empty")
        if not (0.5 <= similarity <= 1.0):
            raise ValueError("similarity must be in [0.5, 1.0]")
        root = self.client.get_json_root(
            "getTargetByCompound",
            {"smiles": smiles.strip(), "cutoff": similarity})
        rows = []
        for raw in root.get("bdb.affinities", []) or []:
            rows.append({
                "monomer_id": _as_str(raw.get("bdb.monomerid")),
                "smiles": raw.get("bdb.smiles"),
                "ligand_name": raw.get("bdb.inhibitor"),
                "target_name": raw.get("bdb.target"),
                "species": raw.get("bdb.species"),
                "affinity_type": raw.get("bdb.affinity_type"),
                "affinity": _as_str(raw.get("bdb.affinity")),
                "tanimoto": _as_str(raw.get("bdb.tanimoto")) or None,
            })
        rows.sort(key=lambda r: (r["target_name"] or "",
                                 r["affinity_type"] or "",
                                 _affinity_sort_key(r["affinity"]),
                                 r["monomer_id"] or ""))
        hit = root.get("bdb.hit")
        return {"hit": int(hit) if _as_str(hit).isdigit() else None,
                "rows": rows}


def _as_str(value) -> str:
    return "" if value is None else str(value).strip()


def _affinity_sort_key(affinity: str | None) -> float:
    """Numeric sort on affinity strings like '10000', '>133000', '<0.5'."""
    if not affinity:
        return float("inf")
    m = re.search(r"[\d.]+(?:[eE][+-]?\d+)?", affinity)
    try:
        return float(m.group(0)) if m else float("inf")
    except ValueError:
        return float("inf")
