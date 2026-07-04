"""mygene_query — batched mygene.info v3 REST client (modernization of the mygene Python client)."""
from . import canonical
from .client import BASE_URL, BATCH_SIZE, MyGeneQueryClient

__version__ = "0.1.0"
__all__ = ["MyGeneQueryClient", "BASE_URL", "BATCH_SIZE", "canonical", "__version__"]
