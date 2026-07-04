"""ols-terms: structured term lookup and fully-paginated descendants/ancestors retrieval
from the EBI Ontology Lookup Service (OLS4) REST API."""

from .client import OLSClient, OLSError, OLSNotFoundError, double_encode_iri
from .records import TermRecord, record_from_v1, parent_ref, canonical_json, RELATIONS
from .api import (
    lookup_term,
    get_related_terms,
    get_descendants,
    get_ancestors,
    RelatedTermsResult,
)

__version__ = "0.1.0"

__all__ = [
    "OLSClient",
    "OLSError",
    "OLSNotFoundError",
    "double_encode_iri",
    "TermRecord",
    "record_from_v1",
    "parent_ref",
    "canonical_json",
    "RELATIONS",
    "lookup_term",
    "get_related_terms",
    "get_descendants",
    "get_ancestors",
    "RelatedTermsResult",
    "__version__",
]
