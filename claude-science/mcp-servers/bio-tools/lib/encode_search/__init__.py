"""encode-search: complete, count-verified retrieval from the ENCODE portal JSON API.

Mirrors the six mcp-tooluniverse-encode methods:
  search_experiments / search_biosamples / list_files (full-paged, count-verified)
  get_experiment / get_file / get_biosample (per-accession detail, stable-field records)
"""
from .client import EncodeClient, EncodeAPIError, Stats
from .records import (experiment_record, file_record, biosample_record,
                      record_for, canonicalize)
from .tool import EncodeSearch

__all__ = ["EncodeClient", "EncodeAPIError", "Stats", "EncodeSearch",
           "experiment_record", "file_record", "biosample_record",
           "record_for", "canonicalize"]
__version__ = "1.0.0"
