"""unibind-tfbs — UniBind direct TF-DNA interaction retrieval (bio-tools fleet).

Two upstream surfaces, both keyless:

* https://unibind.uio.no/api/v1 — DRF REST catalog of ChIP-seq datasets with
  high-confidence TFBS predictions (dataset search + per-dataset detail).
* https://api.genome.ucsc.edu/getData/track against the registered UniBind
  2021 public track hubs (Robust/Permissive collections) — the only keyless
  region-query surface for UniBind TFBSs (UniBind's own REST API has no
  genomic-interval endpoint; verified 2026-06-09).
"""
from .client import (
    PacedJsonClient,
    TransportStats,
    UniBindApiError,
    NotFound,
)
from .tool import (
    HUB_GENOMES,
    search_datasets,
    get_dataset,
    tfbs_in_region,
    make_unibind_client,
    make_ucsc_client,
)

__all__ = [
    "PacedJsonClient", "TransportStats", "UniBindApiError", "NotFound",
    "HUB_GENOMES", "search_datasets", "get_dataset", "tfbs_in_region",
    "make_unibind_client", "make_ucsc_client",
]
__version__ = "0.1.0"
