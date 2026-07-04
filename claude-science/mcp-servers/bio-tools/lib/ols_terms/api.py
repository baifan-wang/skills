"""High-level operations: term lookup and fully-paginated descendants / ancestors retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote

from .client import OLSClient, OLSError, OLSNotFoundError, double_encode_iri
from .records import RELATIONS, TermRecord, parent_ref, record_from_v1

DEFAULT_PAGE_SIZE = 500


@dataclass
class RelatedTermsResult:
    """Result of a descendants / ancestors / etc. retrieval for one root term."""

    root: TermRecord
    relation: str
    total_elements: int
    terms: list[TermRecord] = field(default_factory=list)

    @property
    def term_count(self) -> int:
        return len(self.terms)

    def to_dict(self) -> dict:
        return {
            "root": self.root.to_dict(),
            "relation": self.relation,
            "total_elements": self.total_elements,
            "term_count": self.term_count,
            "terms": [t.to_dict() for t in self.terms],
        }


def _fetch_term_json(client: OLSClient, ontology: str, term_id: str) -> dict:
    """Fetch the raw v1 term JSON for a CURIE (``GO:0006281`` / ``GO_0006281``) or full IRI."""
    if term_id.startswith(("http://", "https://")):
        return client.get_json(
            f"ontologies/{quote(str(ontology), safe='')}/terms/{double_encode_iri(term_id)}")
    data = client.get_json(f"ontologies/{quote(str(ontology), safe='')}/terms",
                           params={"obo_id": term_id})
    page = data.get("page", {})
    terms = data.get("_embedded", {}).get("terms", [])
    if not terms or int(page.get("totalElements", 0)) == 0:
        raise OLSNotFoundError(f"Term {term_id!r} not found in ontology {ontology!r}")
    if len(terms) > 1:
        terms = sorted(
            terms,
            key=lambda t: (not bool(t.get("is_defining_ontology", False)), t.get("iri", "")),
        )
    return terms[0]


def _paginate(client: OLSClient, path: str, page_size: int) -> tuple[list[dict], int]:
    """Retrieve every page of a paged v1 terms collection.

    Returns ``(raw_terms, total_elements)`` where ``total_elements`` is the count reported
    by the API on the first page.
    """
    page_num = 0
    raw_terms: list[dict] = []
    total: int | None = None
    while True:
        data = client.get_json(path, params={"size": page_size, "page": page_num})
        page = data.get("page", {})
        if total is None:
            total = int(page.get("totalElements", 0))
        batch = data.get("_embedded", {}).get("terms", [])
        raw_terms.extend(batch)
        total_pages = int(page.get("totalPages", 0))
        page_num += 1
        if page_num >= total_pages or not batch:
            break
    return raw_terms, int(total or 0)


def get_term_parents(client: OLSClient, ontology: str, iri: str, page_size: int = DEFAULT_PAGE_SIZE) -> list[dict]:
    """Direct parents of a term as compact ``{curie, iri, label}`` references (sorted)."""
    path = f"ontologies/{quote(str(ontology), safe='')}/terms/{double_encode_iri(iri)}/parents"
    try:
        raw_terms, _total = _paginate(client, path, page_size)
    except OLSNotFoundError:
        return []
    refs = [parent_ref(t) for t in raw_terms]
    return sorted(refs, key=lambda p: (p.get("curie") or "", p.get("iri") or ""))


def lookup_term(
    client: OLSClient,
    ontology: str,
    term_id: str,
    include_parents: bool = True,
) -> TermRecord:
    """Look up a single term by CURIE or IRI within one ontology."""
    term = _fetch_term_json(client, ontology, term_id)
    parents = get_term_parents(client, ontology, term["iri"]) if include_parents else None
    return record_from_v1(term, parents=parents)


def get_related_terms(
    client: OLSClient,
    ontology: str,
    term_id: str,
    relation: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    include_parents: bool = False,
    strict: bool = True,
) -> RelatedTermsResult:
    """Retrieve the complete set of related terms (all pages) for one root term.

    ``relation`` is one of ``ols_terms.RELATIONS`` (descendants, ancestors,
    hierarchicalDescendants, hierarchicalAncestors, parents, children, ...).

    Records are de-duplicated by IRI and returned in deterministic order
    (sorted by CURIE, then IRI). With ``strict=True`` (default) an ``OLSError``
    is raised if the number of unique retrieved terms does not equal the
    ``page.totalElements`` reported by the API.
    """
    if relation not in RELATIONS:
        raise ValueError(f"Unknown relation {relation!r}; expected one of {RELATIONS}")
    root_json = _fetch_term_json(client, ontology, term_id)
    root = record_from_v1(root_json)
    path = (f"ontologies/{quote(str(ontology), safe='')}/terms/"
            f"{double_encode_iri(root.iri)}/{relation}")
    raw_terms, total = _paginate(client, path, page_size)

    seen: set[str] = set()
    records: list[TermRecord] = []
    for t in raw_terms:
        iri = t["iri"]
        if iri in seen:
            continue
        seen.add(iri)
        parents = get_term_parents(client, ontology, iri, page_size) if include_parents else None
        records.append(record_from_v1(t, parents=parents))
    records.sort(key=lambda r: (r.curie or "", r.iri))

    if strict and len(records) != total:
        raise OLSError(
            f"Pagination mismatch for {path}: retrieved {len(records)} unique terms "
            f"but the API reported totalElements={total}"
        )
    return RelatedTermsResult(root=root, relation=relation, total_elements=total, terms=records)


def get_descendants(
    client: OLSClient,
    ontology: str,
    term_id: str,
    hierarchical: bool = False,
    **kwargs,
) -> RelatedTermsResult:
    """All descendants of a term (``hierarchical=True`` follows part_of etc. in addition to is_a)."""
    relation = "hierarchicalDescendants" if hierarchical else "descendants"
    return get_related_terms(client, ontology, term_id, relation, **kwargs)


def get_ancestors(
    client: OLSClient,
    ontology: str,
    term_id: str,
    hierarchical: bool = False,
    **kwargs,
) -> RelatedTermsResult:
    """All ancestors of a term (``hierarchical=True`` follows part_of etc. in addition to is_a)."""
    relation = "hierarchicalAncestors" if hierarchical else "ancestors"
    return get_related_terms(client, ontology, term_id, relation, **kwargs)
