"""grants-gov-search — complete, count-verified Grants.gov funding-opportunity search.

Mirrors the knowledgebase MCP method ``bc_search_grants_gov`` as a standalone
bio-tools client (new-tool track).
"""
from .client import (API_URL, GrantsGovClient, GrantsGovError,
                     IncompleteRetrievalError, SearchResult)
from .records import canonical_json, canonical_records
from .spec import ALL_STATUSES, DEFAULT_STATUSES, VALID_STATUSES, GrantsSearchSpec

__all__ = [
    "API_URL", "GrantsGovClient", "GrantsGovError", "IncompleteRetrievalError",
    "SearchResult", "canonical_json", "canonical_records",
    "GrantsSearchSpec", "ALL_STATUSES", "DEFAULT_STATUSES", "VALID_STATUSES",
]
__version__ = "0.1.0"
