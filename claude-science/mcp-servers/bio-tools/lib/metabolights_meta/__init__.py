"""metabolights_meta — structured study metadata retrieval from the MetaboLights web service.

Public API:
    MetaboLightsClient        — rate-limited, retrying HTTP client for www.ebi.ac.uk/metabolights/ws
    get_study_metadata        — one accession  -> structured metadata record
    get_studies_metadata      — accession list -> list of records (deterministic order)
    list_public_studies       — full public study accession list (sorted, with API-reported count)
    extract_study_metadata    — pure function: raw ISA-JSON payload -> metadata record
    canonical_json            — deterministic JSON serialization used for hashing/diffing
"""

from .client import (
    MetaboLightsClient,
    MetaboLightsError,
    MetaboLightsHTTPError,
    MetaboLightsNotFoundError,
)
from .meta import (
    canonical_json,
    extract_study_metadata,
    get_studies_metadata,
    get_study_metadata,
    list_public_studies,
)
from .files import (
    get_study_files,
    search_data_files,
)

__version__ = "0.2.0"

__all__ = [
    "MetaboLightsClient",
    "MetaboLightsError",
    "MetaboLightsHTTPError",
    "MetaboLightsNotFoundError",
    "canonical_json",
    "extract_study_metadata",
    "get_studies_metadata",
    "get_study_files",
    "get_study_metadata",
    "list_public_studies",
    "search_data_files",
    "__version__",
]
