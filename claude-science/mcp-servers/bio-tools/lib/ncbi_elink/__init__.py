"""ncbi_elink - structured cross-database link retrieval via NCBI E-utilities elink."""
from .client import EUtilsClient
from .elink import (canonical_json, elink_links, enumerate_linknames,
                    parse_einfo_linklist, parse_linksets, resolve_accessions)

__all__ = ["EUtilsClient", "canonical_json", "elink_links", "enumerate_linknames",
           "parse_einfo_linklist", "parse_linksets", "resolve_accessions"]
__version__ = "0.1.0"
