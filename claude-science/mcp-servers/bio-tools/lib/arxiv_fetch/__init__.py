"""arxiv-fetch — arXiv Atom API retrieval (bio-tools fleet).

Search + batch metadata fetch over http://export.arxiv.org/api/query,
paced >= 3 s between requests per the arXiv API terms of use.
"""
from .client import ArxivClient, ArxivApiError
from .tool import ArxivFetch, parse_feed, SORT_BY, SORT_ORDER

__all__ = ["ArxivClient", "ArxivApiError", "ArxivFetch", "parse_feed",
           "SORT_BY", "SORT_ORDER"]
__version__ = "0.1.0"
