"""kegg-fetch: batched KEGG REST retrieval.

Modernizes the serial Bio.KEGG.REST.kegg_get() pattern (one entry per HTTP
request) into batched /get calls of up to 10 entries per request, returning
both the raw KEGG flat-file record and a compact structured dict per entry.

KEGG REST is provided for academic use only (https://www.kegg.jp/kegg/rest/).
"""

from .canonical import canonicalize
from .client import MAX_BATCH, KeggClient, KeggEntry, KeggError
from .parse import parse_entry, parse_fields, split_flat

__version__ = "0.1.0"

__all__ = [
    "KeggClient",
    "KeggEntry",
    "KeggError",
    "MAX_BATCH",
    "canonicalize",
    "parse_entry",
    "parse_fields",
    "split_flat",
    "__version__",
]
