"""uniprot-fetch: batched UniProtKB retrieval (FASTA + flat-file), split back per accession.

Modernizes the legacy serial per-accession pattern
(GET https://rest.uniprot.org/uniprotkb/<acc>.fasta and <acc>.txt in a loop;
equivalently Bio.ExPASy.get_sprot_raw per accession) into batched
`accession:` OR-queries against the UniProt REST search endpoint with cursor
pagination, gzip transfer, retries, and deterministic input-order output.
"""

from .client import UniProtClient
from .canonicalize import canonicalize_fasta, canonicalize_flatfile
from .split import (
    fasta_accession,
    flatfile_primary_accession,
    split_fasta,
    split_flatfile,
)

__version__ = "0.1.0"

__all__ = [
    "UniProtClient",
    "split_fasta",
    "split_flatfile",
    "fasta_accession",
    "flatfile_primary_accession",
    "canonicalize_fasta",
    "canonicalize_flatfile",
    "__version__",
]
