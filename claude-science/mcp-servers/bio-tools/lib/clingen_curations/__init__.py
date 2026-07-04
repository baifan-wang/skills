"""clingen-curations — complete, count-verified retrieval of ClinGen curations.

Mirrors the 8 tooluniverse/clingen MCP methods:
gene validity (search + bulk), dosage sensitivity (search + bulk + regions),
clinical actionability (adult / pediatric / search), variant classifications.
"""
from .client import ClinGenClient, ClinGenApiError, NotFound, TransportStats
from .tool import ClinGenCurations
from .records import (
    canonicalize,
    validity_record,
    dosage_record,
    actionability_record,
    erepo_record,
    normalize_dosage_assertion,
    DOSAGE_ASSERTION_LABELS,
)

__version__ = "0.1.0"
__all__ = [
    "ClinGenClient", "ClinGenApiError", "NotFound", "TransportStats",
    "ClinGenCurations", "canonicalize",
    "validity_record", "dosage_record", "actionability_record", "erepo_record",
    "normalize_dosage_assertion", "DOSAGE_ASSERTION_LABELS",
]
