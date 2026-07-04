"""chembl_bioactivity — direct batched ChEMBL REST retrieval.

Modern replacement for the chembl_webresource_client lazy-pagination pattern
(20 records per HTTP request). Uses limit=1000 paging, optional field
selection, bounded retries with backoff, and deterministic record ordering.
"""
from .client import ChEMBLClient, Instrumentation
from .canonical import canonicalize_record, canonicalize_records, drop_keys

__all__ = [
    "ChEMBLClient",
    "Instrumentation",
    "canonicalize_record",
    "canonicalize_records",
    "drop_keys",
]
__version__ = "0.1.0"
