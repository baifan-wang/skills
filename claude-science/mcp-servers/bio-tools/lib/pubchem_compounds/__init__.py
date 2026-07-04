"""pubchem-compounds — fleet retrieval package for PubChem PUG REST.

Small-molecule lookup: identifier resolution (name/SMILES/InChIKey -> CID),
computed properties, synonyms, bioassay activity summaries, 2D similarity
search and GHS safety classification.
"""

from .client import NotFound, PubChemApiError, PugRestClient
from .tool import PubChemCompounds

__all__ = ["PubChemCompounds", "PugRestClient", "PubChemApiError", "NotFound"]
__version__ = "0.1.0"
