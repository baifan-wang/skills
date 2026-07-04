"""depmap-models: Sanger Cell Model Passports retrieval tool (bio-tools fleet)."""

from .client import API_BASE, CMPClient, CMPError
from .records import canonical_json
from .tool import DepMapModels

__version__ = "0.1.0"
__all__ = ["DepMapModels", "CMPClient", "CMPError", "API_BASE",
           "canonical_json", "__version__"]
