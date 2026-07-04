"""gtex-expression — complete, count-verified GTEx Portal API v2 retrieval."""
from .client import GtexApiError, GtexClient, NotFound, TransportStats
from .tool import (CountMismatch, DEFAULT_DATASET, GtexExpression, canonicalize)

__all__ = ["GtexApiError", "GtexClient", "NotFound", "TransportStats",
           "CountMismatch", "DEFAULT_DATASET", "GtexExpression", "canonicalize"]
__version__ = "0.1.0"
