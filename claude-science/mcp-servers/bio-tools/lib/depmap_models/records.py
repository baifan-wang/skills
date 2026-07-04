"""Record shaping + canonicalization for depmap-models.

Canonicalization rules (documented in README, enforced here):
  * JSON with sorted keys, UTF-8, compact separators when hashing.
  * `names` lists sorted case-insensitively (upstream order is not guaranteed).
  * Volatile/availability-churn booleans are RETAINED (they are scientific
    metadata about what data exists for a model) — nothing scientific dropped.
  * JSON:API plumbing (`links`, `jsonapi`, `relationships` link blocks) never
    enters a record.
  * Dependency rows sorted by (model_id, source); float fields kept verbatim.
"""

from __future__ import annotations

import json
from typing import Any

MODEL_ATTRS = [
    "model_type", "growth_properties", "model_treatment",
    "msi_status", "ploidy_wes", "ploidy_wgs", "mutations_per_mb",
    "tissue", "cancer_type", "sample_id",
    "mutations_available", "cnv_available", "expression_available",
    "rnaseq_available", "crispr_ko_available", "drugs_available",
    "fusions_available", "methylation_available", "proteomics_available",
    "commercial_available",
]


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def shape_model(data: dict[str, Any],
                included: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """JSON:API model resource (+optional included) -> flat stable record."""
    attrs = data.get("attributes", {})
    rec: dict[str, Any] = {
        "model_id": data["id"],
        "names": sorted(attrs.get("names") or [], key=str.casefold),
        "model_type": attrs.get("model_type"),
        "growth_properties": attrs.get("growth_properties"),
        "model_treatment": attrs.get("model_treatment"),
        "ploidy_wes": attrs.get("ploidy_wes"),
        "ploidy_wgs": attrs.get("ploidy_wgs"),
        "mutations_per_mb": attrs.get("mutations_per_mb"),
        "msi_status": None,
        "tissue": None,
        "cancer_type": None,
        "sample_id": None,
    }
    for key in ("mutations_available", "cnv_available", "expression_available",
                "rnaseq_available", "crispr_ko_available", "drugs_available",
                "fusions_available", "methylation_available",
                "proteomics_available", "commercial_available"):
        rec[key] = attrs.get(key)

    for inc in included or []:
        t = inc.get("type")
        a = inc.get("attributes", {})
        if t == "tissue":
            rec["tissue"] = a.get("name")
        elif t == "cancer_type":
            rec["cancer_type"] = a.get("name")
        elif t == "model_msi_status" and a.get("current"):
            rec["msi_status"] = a.get("msi_status")
        elif t == "sample":
            rec["sample_id"] = inc.get("id")
    return rec


def shape_model_row(data: dict[str, Any]) -> dict[str, Any]:
    """List-row shaping (no includes): id + names + availability flags."""
    attrs = data.get("attributes", {})
    return {
        "model_id": data["id"],
        "names": sorted(attrs.get("names") or [], key=str.casefold),
        "model_type": attrs.get("model_type"),
        "growth_properties": attrs.get("growth_properties"),
        "crispr_ko_available": attrs.get("crispr_ko_available"),
        "rnaseq_available": attrs.get("rnaseq_available"),
        "mutations_available": attrs.get("mutations_available"),
    }


def shape_gene(data: dict[str, Any]) -> dict[str, Any]:
    attrs = data.get("attributes", {})
    return {
        "gene_id": data["id"],
        "symbol": attrs.get("symbol"),
        "hgnc_id": attrs.get("hgnc_id"),
        "hgnc_status": attrs.get("hgnc_status"),
        "location": attrs.get("location"),
        "cancer_driver": attrs.get("cancer_driver"),
        "tumour_suppressor": attrs.get("tumour_suppressor"),
        "in_yusa_lib": attrs.get("in_yusa_lib"),
    }


def shape_dependency(data: dict[str, Any]) -> dict[str, Any]:
    """One crispr_ko row -> stable record. Row id is an internal surrogate
    key (volatile across reloads) and is dropped; identity = (gene, model,
    source)."""
    attrs = data.get("attributes", {})
    rels = data.get("relationships", {})

    def rel_id(name: str) -> str | None:
        d = (rels.get(name) or {}).get("data") or {}
        return d.get("id")

    return {
        "gene_id": rel_id("gene"),
        "model_id": rel_id("model"),
        "source": attrs.get("source"),
        "bf": attrs.get("bf"),
        "bf_scaled": attrs.get("bf_scaled"),
        "fc_clean": attrs.get("fc_clean"),
        "fc_clean_qn": attrs.get("fc_clean_qn"),
        "mageck_fdr": attrs.get("mageck_fdr"),
        "qc_pass": attrs.get("qc_pass"),
    }


def sort_dependencies(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (r["model_id"] or "", r["source"] or ""))
