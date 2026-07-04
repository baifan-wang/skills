"""gwas-catalog — honest retrieval from the NHGRI-EBI GWAS Catalog REST API v2."""
from .client import GwasApiError, GwasClient, NotFound, TransportStats
from .tool import (ALLOWED_FILTERS, CountMismatch, FilterIgnored, GwasCatalog,
                   flatten_association, flatten_efo_trait, flatten_snp,
                   flatten_study)

__all__ = ["GwasApiError", "GwasClient", "NotFound", "TransportStats",
           "ALLOWED_FILTERS", "CountMismatch", "FilterIgnored", "GwasCatalog",
           "flatten_association", "flatten_efo_trait", "flatten_snp",
           "flatten_study"]
__version__ = "0.1.0"
