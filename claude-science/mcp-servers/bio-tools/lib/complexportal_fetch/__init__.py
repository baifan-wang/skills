"""complexportal-fetch: structured access to the EBI Complex Portal web service.

Complex AC (CPX-...) list or participant UniProt accession -> structured complex
records (complex AC, recommended name, species, participants with stoichiometry,
evidence ECO code, GO annotations, cross-references), with deterministic ordering,
complete pagination and polite retries.
"""
from .client import ComplexPortalClient, NotFoundError, ComplexPortalError
from .fetch import fetch_complex, fetch_complexes, search_by_participant
from .table import records_to_tsv, search_to_tsv, records_to_json

__version__ = "0.1.0"

__all__ = [
    "ComplexPortalClient",
    "NotFoundError",
    "ComplexPortalError",
    "fetch_complex",
    "fetch_complexes",
    "search_by_participant",
    "records_to_tsv",
    "search_to_tsv",
    "records_to_json",
]
