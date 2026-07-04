"""interpro-entry-search — entry-centric InterPro/Pfam retrieval.

Public surface (mirrors the 7 entry-centric MCP methods):

* :func:`search_entries`   — InterPro/member-DB entry keyword search (complete cursor walk)
* :func:`get_entry`        — entry detail for an IPR or PF accession
* :func:`search_clans`     — Pfam clan (set) keyword search
* :func:`clan_members`     — member families of a clan (also covers clan detail)
* :func:`entry_proteins`   — member proteins of a Pfam family (count or full walk)
* :func:`entry_proteomes`  — proteomes containing members of a Pfam family

The per-PROTEIN direction (protein -> domain architecture) lives in the
sibling tool ``interpro-domains`` and is intentionally NOT duplicated here.
"""

from __future__ import annotations

from .client import (
    AccessionNotFound,
    InterProEntryClient,
    InterProError,
)
from .summary import (
    canonical_json,
    digest,
    summarize_clan_detail,
    summarize_clan_search,
    summarize_entry_detail,
    summarize_proteins,
    summarize_proteomes,
    summarize_search,
)

__version__ = "0.1.0"

__all__ = [
    "AccessionNotFound",
    "InterProEntryClient",
    "InterProError",
    "search_entries",
    "get_entry",
    "search_clans",
    "clan_members",
    "entry_proteins",
    "entry_proteomes",
    "canonical_json",
    "digest",
]


def _with_client(client, fn):
    own = client is None
    client = client or InterProEntryClient()
    try:
        return fn(client)
    finally:
        if own:
            client.close()


def search_entries(q=None, entry_type=None, source_db="interpro", go_term=None, client=None):
    """Complete keyword search -> {"count", "results"} (deterministic summary)."""
    return _with_client(
        client,
        lambda c: summarize_search(
            c.search_entries(q=q, entry_type=entry_type, source_db=source_db, go_term=go_term)
        ),
    )


def get_entry(accession, client=None):
    """Entry detail (IPR or PF) -> deterministic summary record."""
    return _with_client(client, lambda c: summarize_entry_detail(c.get_entry(accession)))


def search_clans(q=None, client=None):
    """Pfam clan search -> {"count", "results"}; empty result -> count=0."""
    return _with_client(client, lambda c: summarize_clan_search(c.search_clans(q=q)))


def clan_members(clan_acc, client=None):
    """Clan detail incl. complete sorted member list."""
    return _with_client(client, lambda c: summarize_clan_detail(c.get_clan(clan_acc)))


def entry_proteins(pf_acc, reviewed_only=False, tax_id=None, count_only=False, client=None):
    """Member proteins of a Pfam family. count_only=True for very large families."""
    return _with_client(
        client,
        lambda c: summarize_proteins(
            c.entry_proteins(
                pf_acc, reviewed_only=reviewed_only, tax_id=tax_id, count_only=count_only
            )
        ),
    )


def entry_proteomes(pf_acc, count_only=False, client=None):
    """Proteomes containing members of a Pfam family."""
    return _with_client(
        client,
        lambda c: summarize_proteomes(c.entry_proteomes(pf_acc, count_only=count_only)),
    )
