"""pubmed-fetch: batched PubMed retrieval via NCBI E-utilities (epost + efetch).

Modernizes the serial ``Bio.Entrez.efetch(db="pubmed", id=<one pmid>)`` pattern into
a single epost + batched efetch (200 PMIDs/request) workflow, returning per-PMID XML
records and structured JSON records.
"""

from .fetch import PubMedFetcher, PubMedFetchError, FetchStats
from .parse import parse_article, parse_articleset
from .canonical import canonicalize, extract_articles

__version__ = "0.1.0"

__all__ = [
    "PubMedFetcher",
    "PubMedFetchError",
    "FetchStats",
    "parse_article",
    "parse_articleset",
    "canonicalize",
    "extract_articles",
    "__version__",
]
