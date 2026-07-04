"""gnomad-variants — gnomAD GraphQL retrieval tool (bio-tools fleet).

Mirrors the 10 tooluniverse/gnomad MCP methods: variant lookup, variant
search, gene variants, gene constraint, region variants, liftover, ClinVar
variants, structural variants (list + single), mitochondrial variants.
"""
from .client import GnomadClient, GnomadApiError, NotFound, TransportStats
from .tool import GnomadVariants, DATASETS, SV_DATASETS, DEFAULT_DATASET
from .records import canonicalize

__all__ = [
    "GnomadClient", "GnomadApiError", "NotFound", "TransportStats",
    "GnomadVariants", "DATASETS", "SV_DATASETS", "DEFAULT_DATASET",
    "canonicalize",
]
__version__ = "0.1.0"
