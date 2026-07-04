"""Per-project protein listing (PRIDE Affinity Proteomics service).

Closes the PARTIAL coverage item bc_search_pride_proteins:
  search_project_proteins(project_accession, keyword=None)
      -> GET /pride-ap/search/proteins

Scope, established by live probing (2026-06-08):
  * The legacy archive-wide ``proteinevidences`` routes (v2
    ``/proteinevidences?projectAccession=`` and nested
    ``/projects/{acc}/proteinevidences``) NO LONGER EXIST — the v2 base now
    proxies to the v3 service, whose OpenAPI document lists neither route, and
    both return 404 for valid PXD accessions.
  * Per-project protein listings ARE available for PRIDE Affinity Proteomics
    projects (PAD accessions) via /pride-ap/search/proteins. PXD (MS) projects
    return an empty list there — protein-level results for those live in
    per-file mzTab/mzIdentML submissions, not in a queryable API.
  * The inverse direction (protein -> projects) for the MS archive is
    /proteins/search?accession=...; exposed here as find_projects_for_protein.

Response rows carry {proteinAccession, proteinName, gene, projectCount};
an empty result for a valid project accession is a normal outcome (MS-only
project or no protein table) and is reported as n_proteins=0, not an error.
"""

from __future__ import annotations

from typing import Any

from .client import PrideClient

AP_PROTEIN_SEARCH_PATH = "/pride-ap/search/proteins"
PROTEIN_SEARCH_PATH = "/proteins/search"
PAGE_SIZE = 100


def search_project_proteins(
    project_accession: str,
    keyword: str | None = None,
    client: PrideClient | None = None,
) -> dict[str, Any]:
    """All protein rows for one project from the affinity-proteomics service.

    Pages through /pride-ap/search/proteins (pageSize 100) until an empty
    page; rows are sorted by protein accession. ``keyword`` (optional) is the
    server-side filter (matches accession, gene symbol, or protein name).
    """
    own = client is None
    client = client or PrideClient()
    try:
        proteins: list[dict[str, Any]] = []
        page = 0
        while True:
            params: dict[str, Any] = {
                "projectAccession": project_accession,
                "pageSize": PAGE_SIZE,
                "page": page,
            }
            if keyword is not None:
                params["keyword"] = keyword
            resp = client.get(AP_PROTEIN_SEARCH_PATH, params=params)
            rows = resp.json() if resp.content.strip() else []
            if not rows:
                break
            for row in rows:
                proteins.append({
                    "protein_accession": row.get("proteinAccession"),
                    "protein_name": row.get("proteinName"),
                    "gene": row.get("gene"),
                    "project_count": row.get("projectCount"),
                })
            if len(rows) < PAGE_SIZE:
                break
            page += 1
        proteins.sort(key=lambda p: p["protein_accession"] or "")
        return {
            "project_accession": project_accession,
            "keyword": keyword,
            "n_proteins": len(proteins),
            "proteins": proteins,
        }
    finally:
        if own:
            client.close()


def find_projects_for_protein(
    protein_accession: str,
    client: PrideClient | None = None,
) -> dict[str, Any]:
    """Projects containing a given protein accession (MS archive direction).

    GET /proteins/search?accession=... — the complementary route for PXD
    projects, where per-project protein listings are not served (see module
    docstring). Project lists are sorted.
    """
    own = client is None
    client = client or PrideClient()
    try:
        resp = client.get(PROTEIN_SEARCH_PATH,
                          params={"accession": protein_accession})
        rows = resp.json() if resp.content.strip() else []
        records = [{
            "protein_accession": r.get("proteinAccession"),
            "n_projects": len(r.get("projects") or []),
            "projects": sorted(r.get("projects") or []),
        } for r in rows]
        records.sort(key=lambda r: r["protein_accession"] or "")
        return {
            "query_accession": protein_accession,
            "n_records": len(records),
            "records": records,
        }
    finally:
        if own:
            client.close()
