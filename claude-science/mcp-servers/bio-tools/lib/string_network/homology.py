"""STRING homology (Smith-Waterman bitscore) retrieval.

Closes the GAP coverage item bc_get_string_similarity_scores:
  get_similarity_scores()       -> /api/json/homology       (within/between the
                                   submitted proteins; sparse all-vs-all matrix)
  get_best_similarity_hits()    -> /api/json/homology_best  (best hit per input
                                   protein in a target species)

Upstream quirks handled here:
  * /homology returns ``bitscore`` as a STRING ("406.8") while /homology_best
    returns a NUMBER (598.2) — both are normalized to float.
  * the matrix is sparse: pairs below STRING's similarity floor are simply
    absent (no zero rows), and self-scores ARE included; callers must not
    interpret a missing pair as bitscore 0 — it is "below threshold/not
    reported", which is why records carry only observed pairs.
  * both directions (A,B) and (B,A) are returned by the server with equal
    bitscores; output keeps one canonical direction (id_a <= id_b) after
    verifying the two agree (a mismatch raises — it would mean the upstream
    semantics changed).
"""

from __future__ import annotations

import json
from typing import Any

from .client import StringClient, StringApiError
from .core import map_identifiers


def _norm_bitscore(value: Any) -> float:
    """Bitscores arrive as str from /homology and as float from /homology_best."""
    return round(float(value), 1)


def parse_homology_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Canonicalize /homology rows: one record per unordered pair, id_a <= id_b.

    Verifies that the server's two directed rows for each pair agree on the
    bitscore; raises StringApiError on disagreement. Self-pairs appear once.
    Output sorted by (id_a, id_b).
    """
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        id_a, id_b = row["stringId_A"], row["stringId_B"]
        tax_a, tax_b = int(row["ncbiTaxonId_A"]), int(row["ncbiTaxonId_B"])
        score = _norm_bitscore(row["bitscore"])
        if (id_b, tax_b) < (id_a, tax_a):
            id_a, id_b = id_b, id_a
            tax_a, tax_b = tax_b, tax_a
        key = (id_a, id_b)
        rec = {"id_a": id_a, "id_b": id_b, "taxon_a": tax_a, "taxon_b": tax_b,
               "bitscore": score, "self": id_a == id_b}
        prev = seen.get(key)
        if prev is not None and prev["bitscore"] != score:
            raise StringApiError(
                f"asymmetric homology bitscore for {key}: "
                f"{prev['bitscore']} vs {score}")
        seen[key] = rec
    return sorted(seen.values(), key=lambda r: (r["id_a"], r["id_b"]))


def get_similarity_scores(
    symbols: list[str],
    species: int = 9606,
    client: StringClient | None = None,
) -> dict[str, Any]:
    """Smith-Waterman bitscores among the given proteins (STRING /homology).

    Symbols are mapped to STRING IDs first (limit=1, echo_query=1); the
    mapping and any unmapped symbols are part of the result. ``pairs`` holds
    one record per reported unordered pair (including self-scores); pairs
    absent from STRING's similarity data are NOT listed (sparse semantics —
    see module docstring).
    """
    client = client or StringClient()
    mapped, unmapped = map_identifiers(client, symbols, species)
    pairs: list[dict[str, Any]] = []
    if mapped:
        text = client.call(
            "json", "homology",
            {"identifiers": "\r".join(m["string_id"] for m in mapped),
             "species": species},
        )
        pairs = parse_homology_rows(json.loads(text))
    name_by_id = {m["string_id"]: m["preferred_name"] for m in mapped}
    for rec in pairs:
        rec["name_a"] = name_by_id.get(rec["id_a"])
        rec["name_b"] = name_by_id.get(rec["id_b"])
    return {
        "species": species,
        "mapped": mapped,
        "unmapped": unmapped,
        "n_pairs": len(pairs),
        "n_self": sum(1 for p in pairs if p["self"]),
        "pairs": pairs,
    }


def get_best_similarity_hits(
    symbols: list[str],
    species: int = 9606,
    species_b: int | None = None,
    client: StringClient | None = None,
) -> dict[str, Any]:
    """Best homology hit per input protein in a target species (/homology_best).

    ``species_b=None`` asks STRING for the best hit across all species in its
    homology data. Output sorted by query STRING ID.
    """
    client = client or StringClient()
    mapped, unmapped = map_identifiers(client, symbols, species)
    hits: list[dict[str, Any]] = []
    if mapped:
        params: dict[str, Any] = {
            "identifiers": "\r".join(m["string_id"] for m in mapped),
            "species": species,
        }
        if species_b is not None:
            params["species_b"] = species_b
        text = client.call("json", "homology_best", params)
        name_by_id = {m["string_id"]: m["preferred_name"] for m in mapped}
        for row in json.loads(text):
            hits.append({
                "query_id": row["stringId_A"],
                "query_name": name_by_id.get(row["stringId_A"]),
                "query_taxon": int(row["ncbiTaxonId_A"]),
                "hit_id": row["stringId_B"],
                "hit_taxon": int(row["ncbiTaxonId_B"]),
                "bitscore": _norm_bitscore(row["bitscore"]),
            })
        hits.sort(key=lambda h: (h["query_id"], h["hit_id"]))
    return {
        "species": species,
        "species_b": species_b,
        "mapped": mapped,
        "unmapped": unmapped,
        "n_hits": len(hits),
        "hits": hits,
    }
