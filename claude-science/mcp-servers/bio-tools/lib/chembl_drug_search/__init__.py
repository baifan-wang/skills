"""chembl-drug-search — compound search (name / similarity / substructure) and
indication-based drug search with withdrawal flags, over the ChEMBL REST API."""

from .client import (
    ChemblDrugSearchClient,
    ChemblDrugSearchError,
    MoleculeNotFoundError,
    PaginationError,
)
from .records import canonicalize, sort_similarity_records, summarize_warnings

__version__ = "0.1.0"

__all__ = [
    "ChemblDrugSearchClient",
    "ChemblDrugSearchError",
    "MoleculeNotFoundError",
    "PaginationError",
    "canonicalize",
    "sort_similarity_records",
    "summarize_warnings",
]
