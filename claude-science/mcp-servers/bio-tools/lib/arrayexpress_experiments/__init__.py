"""arrayexpress-experiments: complete, structured retrieval from the ArrayExpress
collection of EBI BioStudies (www.ebi.ac.uk/biostudies/api/v1).

Public API
----------
SearchSpec            declarative search specification (facets, free text, date range)
search_experiments()  complete paged retrieval -> list of search records (dicts)
fetch_experiment()    per-accession study JSON -> flattened experiment record (dict)
BioStudiesClient      throttled / retrying HTTP client (instrumented)
canonicalize()        canonical JSON bytes used by the accuracy gate
"""
from .client import BioStudiesClient
from .search import SearchSpec, search_experiments
from .flatten import fetch_experiment, flatten_study, canonicalize
from .files import (
    get_experiment_files,
    get_experiment_samples,
    parse_sdrf,
)

__all__ = [
    "BioStudiesClient",
    "SearchSpec",
    "search_experiments",
    "fetch_experiment",
    "flatten_study",
    "canonicalize",
    "get_experiment_files",
    "get_experiment_samples",
    "parse_sdrf",
]
__version__ = "0.2.0"
