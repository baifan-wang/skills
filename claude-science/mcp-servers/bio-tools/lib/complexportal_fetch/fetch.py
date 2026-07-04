"""Public API: fetch complexes by CPX accession, search complexes by participant."""
from __future__ import annotations

from .client import ComplexPortalClient, NotFoundError
from .parse import parse_complex, parse_search_element, complex_ac_sort_key

DEFAULT_PAGE_SIZE = 50


def fetch_complex(complex_ac: str, client: ComplexPortalClient | None = None) -> dict:
    """Fetch one complex by CPX accession -> structured record (raises NotFoundError)."""
    own = client is None
    client = client or ComplexPortalClient()
    try:
        return parse_complex(client.get_complex(complex_ac))
    finally:
        if own:
            client.close()


def fetch_complexes(complex_acs: list[str], client: ComplexPortalClient | None = None) -> dict:
    """Fetch a list of CPX accessions.

    Returns ``{"records": [...], "not_found": [...]}``. Records are returned in
    the order of the (de-duplicated) input accession list; unknown accessions are
    reported in ``not_found`` rather than silently dropped.
    """
    own = client is None
    client = client or ComplexPortalClient()
    seen: set[str] = set()
    ordered: list[str] = []
    for ac in complex_acs:
        ac = ac.strip()
        if ac and ac not in seen:
            seen.add(ac)
            ordered.append(ac)
    records: list[dict] = []
    not_found: list[str] = []
    try:
        for ac in ordered:
            try:
                records.append(parse_complex(client.get_complex(ac)))
            except NotFoundError:
                not_found.append(ac)
        return {"records": records, "not_found": not_found}
    finally:
        if own:
            client.close()


def search_by_participant(
    accession: str,
    client: ComplexPortalClient | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    participants_only: bool = True,
) -> dict:
    """Search complexes containing a participant accession (UniProt, ChEBI, ...).

    With ``participants_only=True`` (default) the Solr query is field-qualified as
    ``pxref:<accession>`` so only complexes that actually contain the molecule as a
    participant cross-reference are returned.  With ``participants_only=False`` the
    bare accession is submitted, which additionally matches free text (descriptions,
    names) and therefore over-reports.

    All result pages are retrieved; the row count is verified against the
    ``totalNumberOfResults`` reported by the service.  Results are sorted by
    complex accession (numeric).
    """
    own = client is None
    client = client or ComplexPortalClient()
    accession = accession.strip()
    query = f'pxref:"{accession}"' if participants_only else accession
    try:
        elements: list[dict] = []
        first = 0
        total = None
        while True:
            page = client.search(query, first=first, number=page_size)
            total = page.get("totalNumberOfResults", 0)
            batch = page.get("elements") or []
            elements.extend(batch)
            first += len(batch)
            if first >= total or not batch:
                break
        if total is not None and len(elements) != total:
            raise RuntimeError(
                f"pagination mismatch for {query!r}: retrieved {len(elements)} of {total}"
            )
        records = sorted(
            (parse_search_element(e) for e in elements),
            key=lambda r: complex_ac_sort_key(r.get("complex_ac") or ""),
        )
        return {
            "query_accession": accession,
            "solr_query": query,
            "total_reported": total,
            "total_retrieved": len(records),
            "complexes": records,
        }
    finally:
        if own:
            client.close()
