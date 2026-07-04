"""bindingdb-affinities — fleet retrieval package for the BindingDB REST API.

Measured binding affinities (Ki/Kd/IC50/EC50...) between small molecules and
protein targets: ligands for a UniProt target, and targets for a query
compound by 2D similarity.
"""

from .client import BindingDbApiError, BindingDbClient
from .tool import BindingDbAffinities

__all__ = ["BindingDbAffinities", "BindingDbClient", "BindingDbApiError"]
__version__ = "0.1.0"
