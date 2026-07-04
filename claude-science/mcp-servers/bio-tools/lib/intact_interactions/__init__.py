"""intact-interactions: complete, MI-score-filtered binary interaction
retrieval from the IntAct web service (www.ebi.ac.uk/intact/ws)."""

from .client import IntActClient, IntActError
from .core import (
    canonical_json,
    count_interactions_for_interactor,
    fetch_interactions,
    naive_first_page,
    resolve_interactors,
    slim_record,
    sort_records,
)
from .details import (
    build_network,
    get_interaction_details,
    get_interactor,
)

__version__ = "0.2.0"

__all__ = [
    "IntActClient",
    "IntActError",
    "build_network",
    "canonical_json",
    "count_interactions_for_interactor",
    "fetch_interactions",
    "get_interaction_details",
    "get_interactor",
    "naive_first_page",
    "resolve_interactors",
    "slim_record",
    "sort_records",
    "__version__",
]
