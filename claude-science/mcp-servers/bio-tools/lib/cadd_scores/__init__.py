"""cadd-scores — CADD deleteriousness score retrieval (bio-tools fleet).

Mirrors the three tooluniverse/cadd MCP methods:
variant score, all substitutions at a position, range scores (<=100 bp).
"""
from .client import CaddClient, CaddApiError, CaddHttpError
from .tool import (
    CaddScores,
    CaddEmptyResult,
    CaddRefMismatch,
    CaddAltNotFound,
    KNOWN_VERSIONS,
    MAX_RANGE_BP,
)

__all__ = [
    "CaddClient", "CaddApiError", "CaddHttpError",
    "CaddScores", "CaddEmptyResult", "CaddRefMismatch", "CaddAltNotFound",
    "KNOWN_VERSIONS", "MAX_RANGE_BP",
]
__version__ = "1.0.0"
