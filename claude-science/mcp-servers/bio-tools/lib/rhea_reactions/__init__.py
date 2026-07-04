"""rhea-reactions — fleet retrieval package for the Rhea reaction knowledgebase.

Retrieval goes through Rhea's public SPARQL endpoint
(https://sparql.rhea-db.org/sparql) rather than the www.rhea-db.org REST
routes: the web host sits behind a Cloudflare JS challenge that blocks
non-browser clients, while the SPARQL endpoint is keyless, fast and stable
(it is SIB's documented programmatic interface to Rhea RDF).
"""

from .client import RheaApiError, RheaSparqlClient
from .tool import NotFound, RheaReactions, normalize_rhea_id

__all__ = ["RheaReactions", "RheaSparqlClient", "RheaApiError", "NotFound",
           "normalize_rhea_id"]
__version__ = "0.1.0"
