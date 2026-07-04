"""Flattening of MGnify JSON:API resource objects into plain, deterministic records.

These functions are pure (no I/O) so they can be unit-tested offline.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

STUDY_COLUMNS = [
    "accession",
    "secondary_accession",
    "bioproject",
    "study_name",
    "biome_lineages",
    "samples_count",
    "centre_name",
    "data_origination",
    "last_update",
    "analyses_total",
    "analyses_by_pipeline_version",
    "analyses_by_experiment_type",
]

ANALYSIS_COLUMNS = [
    "analysis_accession",
    "study_accession",
    "pipeline_version",
    "experiment_type",
    "analysis_status",
    "run_accession",
    "assembly_accession",
    "sample_accession",
    "instrument_platform",
]

LISTING_COLUMNS = [
    "accession",
    "secondary_accession",
    "bioproject",
    "study_name",
    "biome_lineages",
    "samples_count",
    "centre_name",
    "last_update",
]


def _rel_ids(obj: dict[str, Any], name: str) -> list[str]:
    """Inline related-resource identifiers under ``relationships[name].data`` (sorted)."""
    rel = (obj.get("relationships") or {}).get(name) or {}
    data = rel.get("data")
    if data is None:
        return []
    if isinstance(data, dict):
        return [data["id"]]
    return sorted(d["id"] for d in data)


def _rel_id(obj: dict[str, Any], name: str) -> str | None:
    ids = _rel_ids(obj, name)
    return ids[0] if ids else None


def flatten_study(obj: dict[str, Any]) -> dict[str, Any]:
    """Flatten a ``studies`` resource object (single GET ``data`` or a listing item)."""
    a = obj.get("attributes", {})
    return {
        "accession": obj.get("id") or a.get("accession"),
        "secondary_accession": a.get("secondary-accession"),
        "bioproject": a.get("bioproject"),
        "study_name": a.get("study-name"),
        "biome_lineages": _rel_ids(obj, "biomes"),
        "samples_count": a.get("samples-count"),
        "centre_name": a.get("centre-name"),
        "data_origination": a.get("data-origination"),
        "is_private": a.get("is-private"),
        "last_update": a.get("last-update"),
    }


def flatten_analysis(obj: dict[str, Any], study_accession: str | None = None) -> dict[str, Any]:
    """Flatten an ``analysis-jobs`` resource object into one analysis record."""
    a = obj.get("attributes", {})
    pv = a.get("pipeline-version")
    return {
        "analysis_accession": obj.get("id") or a.get("accession"),
        "study_accession": study_accession or _rel_id(obj, "study"),
        "pipeline_version": str(pv) if pv is not None else None,
        "experiment_type": a.get("experiment-type"),
        "analysis_status": a.get("analysis-status"),
        "run_accession": _rel_id(obj, "run"),
        "assembly_accession": _rel_id(obj, "assembly"),
        "sample_accession": _rel_id(obj, "sample"),
        "instrument_platform": a.get("instrument-platform"),
    }


def analysis_count_breakdowns(analysis_records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Counts of analyses by pipeline version and by experiment type (key-sorted)."""
    by_pipeline = Counter(r["pipeline_version"] or "unknown" for r in analysis_records)
    by_experiment = Counter(r["experiment_type"] or "unknown" for r in analysis_records)
    return {
        "by_pipeline_version": dict(sorted(by_pipeline.items())),
        "by_experiment_type": dict(sorted(by_experiment.items())),
    }


def to_tsv(records: list[dict[str, Any]], columns: list[str]) -> str:
    """Serialize records to a TSV table with a fixed column order.

    Lists are joined with ``|``; dicts are serialized as ``k=v`` pairs joined with ``;``
    in key-sorted order; ``None`` becomes an empty string.
    """
    lines = ["\t".join(columns)]
    for r in records:
        row = []
        for c in columns:
            v = r.get(c)
            if v is None:
                row.append("")
            elif isinstance(v, (list, tuple)):
                row.append("|".join(str(x) for x in v))
            elif isinstance(v, dict):
                row.append(";".join(f"{k}={val}" for k, val in sorted(v.items())))
            else:
                row.append(str(v))
        lines.append("\t".join(row))
    return "\n".join(lines) + "\n"
