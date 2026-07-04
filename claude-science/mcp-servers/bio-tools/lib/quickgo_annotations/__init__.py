"""quickgo_annotations — complete, filterable GO annotation retrieval from QuickGO.

Retrieves the *complete* GO annotation set for UniProt gene products from the
EBI QuickGO services (https://www.ebi.ac.uk/QuickGO/services), with aspect and
evidence filtering, GO term metadata hydration, deterministic record ordering,
rate limiting and retries.
"""
from .client import QuickGOClient, TransportStats
from .queries import AnnotationQuery, EVIDENCE_PRESETS, ASPECTS
from .annotations import fetch_annotations, count_annotations, fetch_annotation_set
from .terms import fetch_term_metadata

__version__ = "0.1.0"

__all__ = [
    "QuickGOClient", "TransportStats",
    "AnnotationQuery", "EVIDENCE_PRESETS", "ASPECTS",
    "fetch_annotations", "count_annotations", "fetch_annotation_set",
    "fetch_term_metadata",
]
