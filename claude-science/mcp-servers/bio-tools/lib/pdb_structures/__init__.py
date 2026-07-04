"""pdb-structures — RCSB PDB metadata retrieval (search + data APIs).

Fleet package: politeness pacing (<= 2 req/s per RCSB host), bounded retries,
count-verified paged search, honest not-found reporting. Metadata only —
structure coordinate files (mmCIF/PDB) are never downloaded.
"""
from .client import PDBClient, PDBError, NotFoundError
from .search import search_structures
from .records import (
    MAX_IDS_PER_CALL,
    fetch_entry_records,
    fetch_entity_records,
    fetch_ligand_records,
)

__all__ = [
    "PDBClient",
    "PDBError",
    "NotFoundError",
    "MAX_IDS_PER_CALL",
    "search_structures",
    "fetch_entry_records",
    "fetch_entity_records",
    "fetch_ligand_records",
]
