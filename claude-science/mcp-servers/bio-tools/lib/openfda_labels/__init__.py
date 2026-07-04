"""openfda_labels — complete, deterministic retrieval of FDA drug product labels.

Declarative spec (active ingredient / brand name, optional route / marketing status)
-> complete paged retrieval from api.fda.gov/drug/label.json -> structured records,
with optional targeted section extraction for token-lean output.
"""

from .spec import build_search, validate_spec
from .client import OpenFDAClient
from .extract import extract_record, extract_sections, WARNING_SECTION_FIELDS
from .runner import run_spec, run_battery

__version__ = "0.1.0"

__all__ = [
    "build_search",
    "validate_spec",
    "OpenFDAClient",
    "extract_record",
    "extract_sections",
    "WARNING_SECTION_FIELDS",
    "run_spec",
    "run_battery",
    "__version__",
]
