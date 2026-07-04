"""geo_meta — structured GEO series/sample metadata without full SOFT downloads.

Given GSE accessions (or a GEO DataSets search spec), retrieve structured series
metadata (title, organism, samples with titles/characteristics, platform,
supplementary file URLs) using NCBI E-utilities (esearch/esummary, db=gds) plus
*targeted* SOFT header retrieval (acc.cgi, view=brief, targ=self / targ=gsm).
No platform records and no data tables are ever downloaded.
"""

from .client import PoliteClient
from .core import fetch_series, fetch_series_batch, search_series, run_battery, canonicalize

__version__ = "0.1.0"

__all__ = [
    "PoliteClient",
    "fetch_series",
    "fetch_series_batch",
    "search_series",
    "run_battery",
    "canonicalize",
    "__version__",
]
