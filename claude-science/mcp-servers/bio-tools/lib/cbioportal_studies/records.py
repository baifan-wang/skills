"""Record shaping for cbioportal-studies.

Rules:
  * Wire plumbing (uniqueSampleKey/uniquePatientKey base64 keys) never enters
    a record.
  * ``allSampleCount`` is DROPPED everywhere: the current public API returns
    a constant 1 for it on both SUMMARY and DETAILED projections (verified
    live 2026-06-10 — msk_impact_2017 reports allSampleCount=1 next to
    sequencedSampleCount=10945). True sample totals come from the
    /studies/{id}/samples META count or sequencedSampleCount.
  * Long free-text descriptions are trimmed to DESCRIPTION_MAX chars in
    listing rows (full text kept on single-study detail).
  * Discrete CNA ``alteration`` codes get a human label alongside the code.
"""

from __future__ import annotations

from typing import Any

DESCRIPTION_MAX = 240

CNA_LABELS = {
    -2: "deep_deletion",
    -1: "shallow_deletion",
    0: "diploid",
    1: "gain",
    2: "amplification",
}


def _trim(text: str | None, limit: int = DESCRIPTION_MAX) -> str | None:
    if text is None or len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "\u2026"


def shape_study_row(raw: dict[str, Any]) -> dict[str, Any]:
    """DETAILED /studies row -> lean listing record."""
    cancer_type = raw.get("cancerType") or {}
    return {
        "study_id": raw.get("studyId"),
        "name": raw.get("name"),
        "description": _trim(raw.get("description")),
        "cancer_type_id": raw.get("cancerTypeId"),
        "cancer_type": cancer_type.get("name"),
        "reference_genome": raw.get("referenceGenome"),
        "pmid": raw.get("pmid"),
        "citation": raw.get("citation"),
        "sequenced_sample_count": raw.get("sequencedSampleCount"),
        "cna_sample_count": raw.get("cnaSampleCount"),
        "structural_variant_count": raw.get("structuralVariantCount"),
    }


def shape_study_detail(raw: dict[str, Any]) -> dict[str, Any]:
    """DETAILED /studies/{id} -> full record (untrimmed description)."""
    rec = shape_study_row(raw)
    rec["description"] = raw.get("description")
    rec.update({
        "public": raw.get("publicStudy"),
        "groups": raw.get("groups"),
        "import_date": raw.get("importDate"),
        "mrna_rnaseq_v2_sample_count": raw.get("mrnaRnaSeqV2SampleCount"),
        "methylation_hm27_sample_count": raw.get("methylationHm27SampleCount"),
        "rppa_sample_count": raw.get("rppaSampleCount"),
        "mass_spectrometry_sample_count": raw.get("massSpectrometrySampleCount"),
        "treatment_count": raw.get("treatmentCount"),
    })
    return rec


def shape_profile(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "molecular_profile_id": raw.get("molecularProfileId"),
        "alteration_type": raw.get("molecularAlterationType"),
        "datatype": raw.get("datatype"),
        "name": raw.get("name"),
        "description": _trim(raw.get("description")),
    }


def shape_mutation(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_id": raw.get("sampleId"),
        "patient_id": raw.get("patientId"),
        "protein_change": raw.get("proteinChange"),
        "mutation_type": raw.get("mutationType"),
        "mutation_status": raw.get("mutationStatus"),
        "chromosome": raw.get("chr"),
        "start_position": raw.get("startPosition"),
        "end_position": raw.get("endPosition"),
        "reference_allele": raw.get("referenceAllele"),
        "variant_allele": raw.get("variantAllele"),
        "variant_type": raw.get("variantType"),
        "ncbi_build": raw.get("ncbiBuild"),
        "protein_pos_start": raw.get("proteinPosStart"),
        "protein_pos_end": raw.get("proteinPosEnd"),
        "tumor_alt_count": raw.get("tumorAltCount"),
        "tumor_ref_count": raw.get("tumorRefCount"),
        "refseq_mrna_id": raw.get("refseqMrnaId"),
    }


def shape_cna(raw: dict[str, Any]) -> dict[str, Any]:
    alteration = raw.get("alteration")
    return {
        "sample_id": raw.get("sampleId"),
        "patient_id": raw.get("patientId"),
        "alteration": alteration,
        "alteration_label": CNA_LABELS.get(alteration),
    }


def shape_clinical_attribute(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "attribute_id": raw.get("clinicalAttributeId"),
        "display_name": raw.get("displayName"),
        "description": _trim(raw.get("description")),
        "datatype": raw.get("datatype"),
        "level": "patient" if raw.get("patientAttribute") else "sample",
        "priority": raw.get("priority"),
    }
