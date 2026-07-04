"""protein-atlas — Human Protein Atlas retrieval tool (bio-tools fleet).

Mirrors the knowledgebase MCP method bc_get_human_protein_atlas_info:
tissue / subcellular / pathology / blood / brain expression summaries and
antibody information per gene, plus column-selected bulk search.
"""
from .client import HpaClient, HpaError, DEFAULT_BASE_URL, WWW_BASE_URL
from .api import ProteinAtlas, AmbiguousSymbolError, SymbolNotFoundError, is_ensg
from .records import summarize, canonicalize, SUMMARY_FIELDS

__version__ = "0.1.0"
__all__ = [
    "HpaClient", "HpaError", "DEFAULT_BASE_URL", "WWW_BASE_URL",
    "ProteinAtlas", "AmbiguousSymbolError", "SymbolNotFoundError", "is_ensg",
    "summarize", "canonicalize", "SUMMARY_FIELDS",
]
