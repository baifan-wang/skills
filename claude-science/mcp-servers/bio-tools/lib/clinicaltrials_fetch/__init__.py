"""clinicaltrials-fetch: declarative, deterministic retrieval from the ClinicalTrials.gov v2 API.

A declarative filter spec (condition, intervention, overall status, phase, study type,
enrollment range, primary completion date range, first-posted date range, location country,
lead sponsor class) is translated into ClinicalTrials.gov v2 API query parameters
(query.cond / query.intr / filter.overallStatus / filter.advanced Essie expressions),
retrieved completely via pageToken pagination, trimmed to a compact per-study record,
sorted by NCT ID, and returned together with a provenance log of every API call made.
"""

from .spec import FilterSpec, DateRange, IntRange
from .query import build_query_params, build_count_params, build_crosscheck_params, build_naive_term
from .client import CTGovClient, DEFAULT_FIELDS
from .records import trim_study
from .postfilter import record_matches
from .fetch import fetch

__version__ = "0.1.0"

__all__ = [
    "FilterSpec", "DateRange", "IntRange",
    "build_query_params", "build_count_params", "build_crosscheck_params", "build_naive_term",
    "CTGovClient", "DEFAULT_FIELDS",
    "trim_study", "record_matches", "fetch",
    "__version__",
]
