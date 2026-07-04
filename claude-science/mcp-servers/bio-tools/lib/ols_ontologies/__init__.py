"""ols-ontologies: structured ontology-level metadata from the EBI OLS4 API.

Covers the ontology catalogue (/api/ontologies), per-ontology metadata
(/api/ontologies/{id}) and term-count verification via
/api/ontologies/{id}/terms?size=1 (page.totalElements).
"""
from .client import OLSClient
from .records import parse_ontology_record, canonicalize, RECORD_FIELDS
from .api import fetch_ontologies, list_catalogue, verify_term_counts

__version__ = "0.1.0"
__all__ = [
    "OLSClient",
    "parse_ontology_record",
    "canonicalize",
    "RECORD_FIELDS",
    "fetch_ontologies",
    "list_catalogue",
    "verify_term_counts",
]
