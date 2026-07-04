"""rfam-families: structured access to the Rfam REST API (https://rfam.org).

Mirrors the 9 tooluniverse/rfam MCP methods:
  family info, seed alignment (stockholm/fasta), covariance model, phylogenetic
  tree, sequence regions, PDB structure mapping, async sequence search (cmscan),
  and accession<->id conversion.

Routes used (content-negotiated via the documented ?content-type= parameter):
  /family/{acc|id}?content-type=application/json   family metadata
  /family/{acc}/alignment?content-type=text/plain        seed alignment (Stockholm)
  /family/{acc}/alignment/fasta?content-type=text/plain  seed alignment (aligned FASTA)
  /family/{acc}/cm?content-type=text/plain                Infernal covariance model
  /family/{acc}/tree?content-type=text/plain              seed phylogenetic tree (NHX)
  /family/{acc}/regions?content-type=text/plain           full-region hit list (TSV)
  /family/{acc}/structures?content-type=application/json  PDB residue mappings
  /family/{acc}/acc , /family/{id}/id                     accession<->id conversion
  POST /search/sequence + poll resultURL                  async single-sequence cmscan
"""
from .client import RfamClient, RfamApiError, NotFound, SearchUnavailable, BASE_URL
from .records import (
    canonicalize_json,
    family_record,
    parse_regions,
    parse_stockholm_seq_names,
    parse_fasta_seq_names,
    parse_cm_header,
    sort_structure_mapping,
    sha256_text,
)
from .tool import RfamFamilies

__version__ = "0.1.0"

__all__ = [
    "RfamClient", "RfamApiError", "NotFound", "SearchUnavailable", "BASE_URL",
    "canonicalize_json", "family_record", "parse_regions",
    "parse_stockholm_seq_names", "parse_fasta_seq_names", "parse_cm_header",
    "sort_structure_mapping", "sha256_text",
    "RfamFamilies", "__version__",
]
