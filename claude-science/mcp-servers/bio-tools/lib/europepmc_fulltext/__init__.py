"""europepmc_fulltext: Europe PMC OA full-text availability check, JATS retrieval and
structured section extraction."""
from .client import EuropePMCClient
from .core import check_availability, fetch_fulltext_xml, fetch_articles, summarize_record
from .extract import extract_sections, normalize_abstract

__all__ = [
    "EuropePMCClient",
    "check_availability",
    "fetch_fulltext_xml",
    "fetch_articles",
    "summarize_record",
    "extract_sections",
    "normalize_abstract",
]
__version__ = "0.1.0"
