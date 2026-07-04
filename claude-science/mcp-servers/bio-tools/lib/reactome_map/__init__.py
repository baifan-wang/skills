"""reactome-map: deterministic gene/protein -> Reactome pathway mapping.

Public API:

- :func:`reactome_map.map_identifiers` — map gene symbols or UniProt accessions
  to Reactome low-level pathways via the AnalysisService token workflow, with a
  ContentService version stamp and a full provenance log.
- :class:`reactome_map.ReactomeClient` — the instrumented HTTP client.
- :func:`reactome_map.stable_view` / :func:`reactome_map.canonical_json` —
  helpers for run-to-run identity checks.
"""
from .client import ReactomeClient, ReactomeHTTPError
from .mapper import canonical_json, compact_view, map_identifiers, stable_view

__version__ = "1.0.0"
__all__ = [
    "ReactomeClient",
    "ReactomeHTTPError",
    "map_identifiers",
    "stable_view",
    "compact_view",
    "canonical_json",
    "__version__",
]
