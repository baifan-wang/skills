"""chebi-ontology — fleet retrieval package for the ChEBI public backend API.

Entity lookup (names, formula, structure, xrefs, ontology relations, roles)
and full-text search over ChEBI (Chemical Entities of Biological Interest).
"""

from .client import ChebiApiError, ChebiClient, NotFound
from .tool import ChebiOntology, normalize_chebi_id

__all__ = ["ChebiOntology", "ChebiClient", "ChebiApiError", "NotFound",
           "normalize_chebi_id"]
__version__ = "0.1.0"
