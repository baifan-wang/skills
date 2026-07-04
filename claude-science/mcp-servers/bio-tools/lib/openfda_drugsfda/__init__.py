"""openfda-drugsfda — complete, verified retrieval from the FDA Drugs@FDA endpoint."""

from .records import canonical_json, normalize_application, sha256_of, to_tsv
from .retrieve import (
    BASE_URL,
    COUNT_FIELDS,
    CountResult,
    MAX_RETRIEVABLE,
    OpenFDADrugsFDAClient,
    ResultSetTooLarge,
    RetrievalResult,
)
from .spec import SearchSpec

__all__ = [
    "BASE_URL",
    "COUNT_FIELDS",
    "CountResult",
    "MAX_RETRIEVABLE",
    "OpenFDADrugsFDAClient",
    "ResultSetTooLarge",
    "RetrievalResult",
    "SearchSpec",
    "canonical_json",
    "normalize_application",
    "sha256_of",
    "to_tsv",
]

__version__ = "0.1.0"
