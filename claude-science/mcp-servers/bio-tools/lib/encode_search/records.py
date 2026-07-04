"""Stable-field record extraction + canonicalization for ENCODE objects.

The full portal JSON for an Experiment embeds every file, replicate, analysis and
audit -- hundreds of KB, much of it volatile (audits get recomputed, analyses get
re-run, schema_version bumps). The record builders below extract a documented
stable subset; `canonicalize` renders any record as deterministic bytes for the
gate's byte-identity checks.

Volatile fields deliberately EXCLUDED from records: audit, analyses,
default_analysis, schema_version, internal_status, internal_tags, submitted_by,
hub, visualize, original_files/contributing_files/revoked_files (file membership
shifts as analyses re-run), documents, references, "@context".
"""
from __future__ import annotations

import json
from typing import Any


def _name(obj: Any) -> Any:
    """Embedded objects may arrive as dicts or @id strings depending on frame."""
    if isinstance(obj, dict):
        return (obj.get("title") or obj.get("term_name") or obj.get("label")
                or obj.get("name") or obj.get("@id"))
    return obj


def experiment_record(doc: dict) -> dict:
    target = doc.get("target") or {}
    bio = doc.get("biosample_ontology") or {}
    return {
        "record_type": "experiment",
        "accession": doc.get("accession"),
        "status": doc.get("status"),
        "assay_term_name": doc.get("assay_term_name"),
        "assay_title": doc.get("assay_title"),
        "target_label": target.get("label") if isinstance(target, dict) else target,
        "biosample_term_name": bio.get("term_name") if isinstance(bio, dict) else bio,
        "biosample_classification": bio.get("classification") if isinstance(bio, dict) else None,
        "biosample_summary": doc.get("biosample_summary"),
        "description": doc.get("description"),
        "lab": _name(doc.get("lab")),
        "award_project": (doc.get("award") or {}).get("project")
                          if isinstance(doc.get("award"), dict) else None,
        "date_released": doc.get("date_released"),
        "date_submitted": doc.get("date_submitted"),
        "assembly": sorted(doc.get("assembly") or []),
        "bio_replicate_count": doc.get("bio_replicate_count"),
        "tech_replicate_count": doc.get("tech_replicate_count"),
        "replication_type": doc.get("replication_type"),
        "dbxrefs": sorted(doc.get("dbxrefs") or []),
        "doi": doc.get("doi"),
        "uuid": doc.get("uuid"),
    }


def file_record(doc: dict) -> dict:
    return {
        "record_type": "file",
        "accession": doc.get("accession"),
        "status": doc.get("status"),
        "file_format": doc.get("file_format"),
        "file_format_type": doc.get("file_format_type"),
        "output_type": doc.get("output_type"),
        "output_category": doc.get("output_category"),
        "assay_term_name": doc.get("assay_term_name"),
        "assembly": doc.get("assembly"),
        "dataset": doc.get("dataset"),
        "biological_replicates": sorted(doc.get("biological_replicates") or []),
        "file_size": doc.get("file_size"),
        "md5sum": doc.get("md5sum"),
        "content_md5sum": doc.get("content_md5sum"),
        "run_type": doc.get("run_type"),
        "read_length": doc.get("read_length"),
        "lab": _name(doc.get("lab")),
        "date_created": doc.get("date_created"),
        "href": doc.get("href"),
        "uuid": doc.get("uuid"),
    }


def biosample_record(doc: dict) -> dict:
    bio = doc.get("biosample_ontology") or {}
    organism = doc.get("organism") or {}
    donor = doc.get("donor") or {}
    return {
        "record_type": "biosample",
        "accession": doc.get("accession"),
        "status": doc.get("status"),
        "term_name": bio.get("term_name") if isinstance(bio, dict) else bio,
        "classification": bio.get("classification") if isinstance(bio, dict) else None,
        "organism": organism.get("scientific_name") if isinstance(organism, dict) else organism,
        "donor": donor.get("accession") if isinstance(donor, dict) else donor,
        "source": _name(doc.get("source")),
        "lab": _name(doc.get("lab")),
        "summary": doc.get("summary"),
        "life_stage": doc.get("life_stage"),
        "age_display": doc.get("age_display"),
        "sex": doc.get("sex"),
        "treatments": sorted(
            t.get("treatment_term_name") for t in doc.get("treatments") or []
            if isinstance(t, dict) and t.get("treatment_term_name")),
        "genetic_modifications": sorted(
            (m.get("@id") if isinstance(m, dict) else m)
            for m in doc.get("genetic_modifications") or []),
        "date_created": doc.get("date_created"),
        "uuid": doc.get("uuid"),
    }


_BUILDERS = {"Experiment": experiment_record, "File": file_record,
             "Biosample": biosample_record}


def record_for(doc: dict) -> dict:
    """Dispatch on the object's @type."""
    for t in doc.get("@type", []):
        if t in _BUILDERS:
            return _BUILDERS[t](doc)
    raise ValueError(f"unsupported @type: {doc.get('@type')}")


def canonicalize(obj: Any) -> bytes:
    """Deterministic byte rendering: sorted keys, no whitespace variance."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":")).encode()
