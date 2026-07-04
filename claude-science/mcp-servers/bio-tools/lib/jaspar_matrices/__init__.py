"""jaspar-matrices — complete, count-verified access to the JASPAR REST API.

Mirrors the 8 tooluniverse/jaspar MCP methods (matrix detail, versions,
species/taxa/collections/releases catalogs, matrix search, full TF profile
listing) against https://jaspar.elixir.no/api/v1.
"""
from .client import JasparClient, JasparApiError, NotFound, TransportStats
from .tool import (
    get_matrix,
    matrix_versions,
    list_matrices,
    list_species,
    list_taxa,
    list_collections,
    list_releases,
)
from .canonical import canonicalize

__version__ = "0.1.0"
__all__ = [
    "JasparClient", "JasparApiError", "NotFound", "TransportStats",
    "get_matrix", "matrix_versions", "list_matrices",
    "list_species", "list_taxa", "list_collections", "list_releases",
    "canonicalize",
]
