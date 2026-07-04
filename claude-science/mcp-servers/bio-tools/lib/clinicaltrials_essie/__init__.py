"""clinicaltrials-essie — Essie-dimension search over the ClinicalTrials.gov v2 API.

Mirrors the mcp-clinical-trials methods NOT covered by clinicaltrials-fetch /
clinicaltrials-results: investigator search, sponsor-name search, eligibility
search, city-level recruiting/location search, and a raw Essie AREA[...]
expression passthrough. All searches are fully paginated (pageToken walk at
pageSize=1000) and totalCount-verified.
"""

from .essie import (
    area_phrase,
    area_term,
    area_range,
    search_location,
    and_join,
    or_join,
    quote_phrase,
)
from .api import (
    search_essie,
    by_investigator,
    by_sponsor_name,
    by_eligibility,
    recruiting_near,
    build_spec_query,
    run_spec,
)
from .client import CTGovClient, BASE_URL

__version__ = "0.1.0"

__all__ = [
    "search_essie", "by_investigator", "by_sponsor_name", "by_eligibility",
    "recruiting_near", "build_spec_query", "run_spec",
    "CTGovClient", "BASE_URL",
    "area_phrase", "area_term", "area_range", "search_location",
    "and_join", "or_join", "quote_phrase",
]
