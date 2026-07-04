"""pubmed-search — PubMed discovery: esearch, ecitmatch, ID conversion, copyright status."""

from .client import (
    ESEARCH_RETSTART_CEILING,
    PubMedSearch,
    PubMedSearchError,
)

__all__ = ["PubMedSearch", "PubMedSearchError", "ESEARCH_RETSTART_CEILING"]
__version__ = "1.0.0"
