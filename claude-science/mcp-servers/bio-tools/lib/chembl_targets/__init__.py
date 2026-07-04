"""chembl-targets: structured access to the ChEMBL target / target_component layer.

Public API:
    ChemblTargetsClient     -- HTTP client (rate-limited, retrying, paginating)
    build_target_record     -- raw API target dict -> structured record
    canonicalize, sha256_of -- canonical bytes / digest of any record structure
    records_to_table        -- structured records -> tidy rows (one per target-component)
    table_to_tsv            -- tidy rows -> TSV text
"""

from .client import (
    ChemblTargetsClient,
    ChemblTargetsError,
    PaginationError,
    TargetNotFoundError,
)
from .records import (
    TABLE_COLUMNS,
    build_target_record,
    canonicalize,
    records_to_table,
    sha256_of,
    table_to_tsv,
)

__version__ = "0.1.0"

__all__ = [
    "ChemblTargetsClient",
    "ChemblTargetsError",
    "PaginationError",
    "TargetNotFoundError",
    "TABLE_COLUMNS",
    "build_target_record",
    "canonicalize",
    "records_to_table",
    "sha256_of",
    "table_to_tsv",
    "__version__",
]
