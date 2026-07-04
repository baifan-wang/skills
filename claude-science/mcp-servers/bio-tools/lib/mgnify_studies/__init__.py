"""mgnify-studies: structured retrieval of MGnify (EBI Metagenomics) study metadata.

Wraps the MGnify JSON:API v1 (https://www.ebi.ac.uk/metagenomics/api/v1) with
complete pagination, deterministic ordering, retries and politeness throttling.
"""

from .client import MGnifyClient, MGnifyError, MGnifyNotFound
from .records import (
    ANALYSIS_COLUMNS,
    LISTING_COLUMNS,
    STUDY_COLUMNS,
    analysis_count_breakdowns,
    flatten_analysis,
    flatten_study,
    to_tsv,
)
from .tool import (
    analyses_tsv,
    fetch_studies,
    fetch_study_analyses,
    listing_tsv,
    search_studies,
    studies_tsv,
)

__version__ = "0.1.0"

__all__ = [
    "MGnifyClient",
    "MGnifyError",
    "MGnifyNotFound",
    "ANALYSIS_COLUMNS",
    "LISTING_COLUMNS",
    "STUDY_COLUMNS",
    "analysis_count_breakdowns",
    "flatten_analysis",
    "flatten_study",
    "to_tsv",
    "analyses_tsv",
    "fetch_studies",
    "fetch_study_analyses",
    "listing_tsv",
    "search_studies",
    "studies_tsv",
    "__version__",
]
