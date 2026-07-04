"""pride-projects: declarative, complete, structured access to PRIDE Archive v2 project metadata."""

from .client import PrideClient, RequestStats
from .records import (
    COMPARABLE_FIELDS,
    comparable_view,
    normalize_detail_record,
    normalize_search_record,
)
from .search import (
    TotalMismatchError,
    build_filter,
    fetch_project,
    fetch_projects,
    search_first_page_naive,
    search_projects,
)
from .proteins import (
    find_projects_for_protein,
    search_project_proteins,
)

__version__ = "0.2.0"

__all__ = [
    "PrideClient",
    "RequestStats",
    "COMPARABLE_FIELDS",
    "comparable_view",
    "normalize_detail_record",
    "normalize_search_record",
    "TotalMismatchError",
    "build_filter",
    "fetch_project",
    "find_projects_for_protein",
    "search_project_proteins",
    "fetch_projects",
    "search_first_page_naive",
    "search_projects",
    "canonicalize",
]


def canonicalize(obj) -> bytes:
    """Stable byte representation of a record / list of records for diffs."""
    import json

    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
