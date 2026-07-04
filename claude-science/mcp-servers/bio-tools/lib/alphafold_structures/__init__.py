"""alphafold-structures — AlphaFold DB prediction metadata (keyless EBI API).

Fleet package: politeness pacing (<= 2 req/s on alphafold.ebi.ac.uk), bounded
retries, honest no-model reporting. Model metadata + download URLs only —
coordinate/PAE payloads are never downloaded.
"""
from .client import AlphaFoldClient, AlphaFoldError, NotFoundError
from .records import (
    MAX_IDS_PER_CALL,
    fetch_coverage_records,
    fetch_prediction_record,
)

__all__ = [
    "AlphaFoldClient",
    "AlphaFoldError",
    "NotFoundError",
    "MAX_IDS_PER_CALL",
    "fetch_coverage_records",
    "fetch_prediction_record",
]
