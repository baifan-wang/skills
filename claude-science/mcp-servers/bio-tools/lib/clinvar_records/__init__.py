"""clinvar-records — direct ClinVar retrieval via NCBI E-utilities (bio-tools fleet).

Complements gnomAD's ClinVar mirror (``mcp_variants.clinvar_variants``) with
the fields the mirror lacks: review status + gold stars, per-classification
last-evaluated dates, submission (SCV) counts, condition/trait sets with
ontology xrefs, and the three 2024+ classification axes (germline, clinical
impact/somatic, oncogenicity).
"""
from .client import ClinVarClient, ClinVarApiError
from .records import gold_stars, parse_summary_doc
from .tool import ClinVarRecords

__all__ = [
    "ClinVarClient", "ClinVarApiError",
    "gold_stars", "parse_summary_doc",
    "ClinVarRecords",
]
__version__ = "0.1.0"
