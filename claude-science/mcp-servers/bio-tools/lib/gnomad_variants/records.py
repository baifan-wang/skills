"""Record normalization and canonicalization.

``canonicalize`` is the single shared function used by the gate, the tests
and the benchmark: deterministic JSON bytes (sorted keys, no whitespace,
ensure_ascii=False). Lists of variant records are sorted by stable keys
before serialization so unordered upstream collections cannot flip the
byte output.
"""
from __future__ import annotations

import json


def canonicalize(obj) -> bytes:
    """Deterministic JSON bytes for equality checks and hashing."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _freq_block(block: dict | None) -> dict | None:
    if block is None:
        return None
    out = {k: block.get(k) for k in
           ("ac", "an", "af", "homozygote_count", "hemizygote_count", "filters")
           if k in block}
    if "filters" in out and out["filters"] is not None:
        out["filters"] = sorted(out["filters"])
    return out


def build_variant_record(v: dict, dataset: str) -> dict:
    return {
        "variant_id": v["variant_id"],
        "dataset": dataset,
        "reference_genome": v.get("reference_genome"),
        "chrom": v.get("chrom"),
        "pos": v.get("pos"),
        "ref": v.get("ref"),
        "alt": v.get("alt"),
        "rsids": sorted(v.get("rsids") or []),
        "exome": _freq_block(v.get("exome")),
        "genome": _freq_block(v.get("genome")),
    }


def build_short_variant_row(v: dict) -> dict:
    """Row shape for gene/region variant listings (lean)."""
    return {
        "variant_id": v["variant_id"],
        "pos": v.get("pos"),
        "ref": v.get("ref"),
        "alt": v.get("alt"),
        "rsids": sorted(v.get("rsids") or []),
        "exome": _freq_block(v.get("exome")),
        "genome": _freq_block(v.get("genome")),
    }


def build_constraint_record(g: dict) -> dict:
    c = g.get("gnomad_constraint") or {}
    return {
        "gene_id": g["gene_id"],
        "symbol": g.get("symbol"),
        "canonical_transcript_id": g.get("canonical_transcript_id"),
        "chrom": g.get("chrom"),
        "start": g.get("start"),
        "stop": g.get("stop"),
        "strand": g.get("strand"),
        "constraint": {k: c.get(k) for k in (
            "exp_lof", "obs_lof", "oe_lof", "oe_lof_lower", "oe_lof_upper",
            "exp_mis", "obs_mis", "oe_mis", "oe_mis_lower", "oe_mis_upper",
            "exp_syn", "obs_syn", "oe_syn", "oe_syn_lower", "oe_syn_upper",
            "pli", "lof_z", "mis_z", "syn_z")},
    }


def build_clinvar_row(v: dict) -> dict:
    return {
        "variant_id": v["variant_id"],
        "clinvar_variation_id": v.get("clinvar_variation_id"),
        "clinical_significance": v.get("clinical_significance"),
        "gold_stars": v.get("gold_stars"),
        "review_status": v.get("review_status"),
        "major_consequence": v.get("major_consequence"),
        "pos": v.get("pos"),
        "transcript_id": v.get("transcript_id"),
        "in_gnomad": v.get("in_gnomad"),
    }


def build_sv_row(v: dict) -> dict:
    out = dict(v)
    if out.get("filters") is not None:
        out["filters"] = sorted(out["filters"])
    if out.get("consequences") is not None:
        out["consequences"] = sorted(
            ({"consequence": c.get("consequence"), "genes": sorted(c.get("genes") or [])}
             for c in out["consequences"]),
            key=lambda c: c["consequence"] or "")
    if out.get("algorithms") is not None:
        out["algorithms"] = sorted(out["algorithms"])
    if out.get("evidence") is not None:
        out["evidence"] = sorted(out["evidence"])
    return out


def build_mito_row(v: dict) -> dict:
    out = {k: v.get(k) for k in ("variant_id", "pos", "ac_het", "ac_hom", "an",
                                 "max_heteroplasmy", "filters")}
    if out.get("filters") is not None:
        out["filters"] = sorted(out["filters"])
    return out


def sort_rows(rows: list[dict]) -> list[dict]:
    """Stable order for variant-row lists: (pos, variant_id)."""
    return sorted(rows, key=lambda r: (r.get("pos") or 0, r["variant_id"]))
