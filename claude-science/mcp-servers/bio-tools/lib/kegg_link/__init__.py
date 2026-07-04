"""kegg_link — batched KEGG REST cross-referencing (/link, /conv, /find) with a tidy mapping table."""

from .client import KeggClient
from .core import (
    LinkResult,
    link,
    conv,
    find,
    filter_exact_symbol,
    gene_ids_by_symbol,
    parse_gene_symbols,
    parse_two_column,
    parse_find,
    records_to_tsv,
    canonicalize_records,
)

__version__ = "0.2.0"

__all__ = [
    "KeggClient",
    "LinkResult",
    "link",
    "conv",
    "find",
    "filter_exact_symbol",
    "gene_ids_by_symbol",
    "parse_gene_symbols",
    "parse_two_column",
    "parse_find",
    "records_to_tsv",
    "canonicalize_records",
]
