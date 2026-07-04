"""string-network: deterministic STRING protein-protein interaction retrieval.

Given gene symbols + an NCBI species ID, the tool
  1. maps symbols to STRING identifiers via /api/json/get_string_ids
     (explicitly reporting any unmapped symbols),
  2. retrieves the interaction network via /api/tsv/network at a stated
     required_score,
  3. emits a structured JSON result with deterministic edge ordering,
     summary statistics, and a provenance log.
"""

from .client import StringClient, StringApiError, DEFAULT_BASE_URL, DEFAULT_CALLER_IDENTITY
from .core import (
    TOOL_NAME,
    TOOL_VERSION,
    build_network,
    canonicalize,
    canonical_edges,
    map_identifiers,
    parse_mapping_rows,
    parse_network_tsv,
    summarize,
)
from .homology import (
    get_best_similarity_hits,
    get_similarity_scores,
    parse_homology_rows,
)

__all__ = [
    "StringClient",
    "StringApiError",
    "DEFAULT_BASE_URL",
    "DEFAULT_CALLER_IDENTITY",
    "TOOL_NAME",
    "TOOL_VERSION",
    "build_network",
    "canonicalize",
    "canonical_edges",
    "get_best_similarity_hits",
    "get_similarity_scores",
    "map_identifiers",
    "parse_homology_rows",
    "parse_mapping_rows",
    "parse_network_tsv",
    "summarize",
]

__version__ = TOOL_VERSION
