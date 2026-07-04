"""emdb-meta: structured metadata retrieval from the EMDB REST API (www.ebi.ac.uk/emdb/api).

EM map *metadata* only — entry records and search; never downloads map volumes.
"""
from .client import EMDBClient
from .records import extract_entry_record, canonicalize
from .search import run_search_spec, search_count
from .sections import (
    extract_publications,
    extract_map_info,
    extract_sample_info,
    extract_imaging_info,
    extract_validation_record,
    fetch_section_records,
    fetch_validation_records,
)

__version__ = "0.2.0"
__all__ = [
    "EMDBClient",
    "extract_entry_record",
    "canonicalize",
    "run_search_spec",
    "search_count",
    "extract_publications",
    "extract_map_info",
    "extract_sample_info",
    "extract_imaging_info",
    "extract_validation_record",
    "fetch_section_records",
    "fetch_validation_records",
]
