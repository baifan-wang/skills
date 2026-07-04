"""biomart_query — direct Ensembl BioMart martservice queries.

Modern replacement for the pybiomart ``Dataset.query()`` pattern: builds the
martservice XML query directly, combines attribute groups that share a filter
specification into the minimal number of HTTP requests, streams TSV, verifies
the completion stamp, retries transient failures, and returns rows in a
deterministic order (sorted by gene ID).
"""

from .client import (
    BiomartClient,
    BiomartError,
    BiomartIncompleteResponse,
    BiomartQueryError,
    QueryResult,
    build_query_xml,
)
from .runner import plan_requests, run_battery
from .introspect import (
    configuration_names,
    list_attributes,
    list_datasets,
    list_filters,
    list_marts,
)

__version__ = "0.2.0"

__all__ = [
    "BiomartClient",
    "BiomartError",
    "BiomartIncompleteResponse",
    "BiomartQueryError",
    "QueryResult",
    "build_query_xml",
    "configuration_names",
    "list_attributes",
    "list_datasets",
    "list_filters",
    "list_marts",
    "plan_requests",
    "run_battery",
    "__version__",
]
