"""panglaodb-markers — cached, checksum-pinned client for the PanglaoDB bulk marker table.

Mirrors the knowledgebase MCP methods bc_get_panglaodb_marker_genes and
bc_get_panglaodb_options without any external MCP dependency.
"""
from .client import (
    MARKER_URL,
    MARKER_SHA256,
    CLIENT_UA,
    ChecksumError,
    default_cache_dir,
    fetch_markers_gz,
)
from .core import (
    COLUMNS,
    NUMERIC_COLUMNS,
    PanglaoDB,
    parse_markers,
)

__version__ = "1.0.0"
__all__ = [
    "MARKER_URL", "MARKER_SHA256", "CLIENT_UA", "ChecksumError",
    "default_cache_dir", "fetch_markers_gz",
    "COLUMNS", "NUMERIC_COLUMNS", "PanglaoDB", "parse_markers",
]
