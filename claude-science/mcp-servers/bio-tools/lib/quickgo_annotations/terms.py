"""GO term metadata lookup via /ontology/go/terms/{ids} (batched)."""
from __future__ import annotations

from urllib.parse import quote

from .client import QuickGOClient

TERMS_CHUNK_SIZE = 50


def fetch_term_metadata(client: QuickGOClient, go_ids: list[str],
                        chunk_size: int = TERMS_CHUNK_SIZE) -> dict[str, dict]:
    """Return {go_id: {id, name, aspect, definition, is_obsolete}} for the given IDs.

    IDs are de-duplicated, sorted, and fetched in chunks of `chunk_size` per
    request. Missing/unresolvable IDs are simply absent from the result.
    """
    ids = sorted({i for i in go_ids if i})
    out: dict[str, dict] = {}
    for start in range(0, len(ids), chunk_size):
        chunk = ids[start:start + chunk_size]
        seg = ','.join(quote(str(i), safe=':') for i in chunk)
        payload = client.get_json(f"/ontology/go/terms/{seg}", {})
        for r in payload.get("results", []):
            out[r["id"]] = {
                "id": r["id"],
                "name": r.get("name"),
                "aspect": r.get("aspect"),
                "definition": (r.get("definition") or {}).get("text"),
                "is_obsolete": r.get("isObsolete", False),
            }
    return out
