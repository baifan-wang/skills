"""dbsnp-records — dbSNP RefSNP retrieval (bio-tools fleet).

Two keyless NCBI surfaces:
- Variation Services (``api.ncbi.nlm.nih.gov/variation/v0/refsnp/{rsid}``)
  for full RefSNP objects (placements, alleles, gene context, frequency
  studies, ClinVar xrefs), distilled to lean JSON-able records.
- E-utilities ``esearch db=snp`` for chromosome-region rsID listings
  (Variation Services has no region-query endpoint).
"""
from .client import DbsnpClient, DbsnpApiError
from .records import distill_refsnp
from .tool import DbsnpRecords

__all__ = ["DbsnpClient", "DbsnpApiError", "distill_refsnp", "DbsnpRecords"]
__version__ = "0.1.0"
