"""mcp-chembl server — tool handlers + stdio entry point.

Tool names/schemas are served verbatim from ``schemas.json`` (captured from
the original hosted connector). Retrieval is delegated to the fleet packages
(chembl-drug-search, chembl-bioactivity, chembl-targets); ``marshal``
reshapes raw ChEMBL REST payloads into the original output formats.
"""

from __future__ import annotations

import urllib.parse
from functools import lru_cache

from mcp_servers_common import Tier1Server, load_schemas
from mcp_servers_common.gate import apply_gate_tier1

from . import marshal

DEFAULT_LIMIT = 20
# Hard ceiling on SMILES similarity/substructure page walks (review
# 3387178880): generic scaffolds match 30k+ molecules; cap >> the 1000
# request limit so ranking is meaningful, with walk_truncated disclosure
# when the upstream match set exceeds it.
SEARCH_WALK_CAP = 10_000


def _limit(args: dict, cap: int = 1000) -> int:
    # args.get(..., default) not `or` — `0 or 20 == 20` would silently coerce
    # limit=0 (review 3377922603); schema minimum is 1, clamp mirrors it.
    return max(1, min(cap, int(args.get("limit", DEFAULT_LIMIT))))


# One client per process; fleet clients handle pacing/retries internally.
@lru_cache(maxsize=1)
def _drugs():
    from chembl_drug_search import ChemblDrugSearchClient
    return ChemblDrugSearchClient()


@lru_cache(maxsize=1)
def _bio():
    from chembl_bioactivity import ChEMBLClient
    return ChEMBLClient()


@lru_cache(maxsize=1)
def _targets():
    from chembl_targets import ChemblTargetsClient
    return ChemblTargetsClient()


def _single_page(client, resource: str, params: dict, limit: int) -> tuple[list, int]:
    """One bounded page via the fleet ChEMBLClient's paced/retrying session,
    with the verified upstream total from page_meta.total_count.

    The original connector used the same single-call pattern but the total it
    reported is preserved here, and every list response additionally carries
    a ``truncated`` flag (see README: deliberate behavior changes).
    """
    from chembl_bioactivity.client import RESOURCES
    collection_key, sort_key = RESOURCES[resource]
    payload = client._get(resource, {**params, "limit": limit, "offset": 0,
                                     "order_by": sort_key})
    meta = payload.get("page_meta") or {}
    return payload.get(collection_key) or [], meta.get("total_count")


# ── compound_search ──────────────────────────────────────────────────────────

def compound_search(args: dict) -> str:
    from chembl_drug_search.client import MoleculeNotFoundError

    limit = _limit(args)
    max_phase = args.get("max_phase")
    client = _drugs()

    if args.get("chembl_id"):
        try:
            records = client.get_molecules([args["chembl_id"]])
        except MoleculeNotFoundError:
            records = []
        if max_phase is not None:
            records = [m for m in records
                       if m.get("max_phase") is not None
                       and float(m["max_phase"]) == float(max_phase)]
        return marshal.compact_json(
            marshal.compound_search_response(records[:limit], len(records)))

    if args.get("smiles"):
        threshold = args.get("similarity_threshold")
        # Through the fleet's dedicated searchers, NOT a raw bounded
        # paginate: these routes reject order_by and their native order is
        # non-contractual, so truncating DURING the walk returned an
        # arbitrary subset instead of the top-N (review 3379150543). The
        # walk itself is hard-ceilinged (review 3387178880: generic
        # scaffolds match 30k+ molecules — never unbounded-by-default on
        # user-shaped SMILES); cap >> limit, ranking is deterministic
        # within the capped set, and truncation is DISCLOSED below.
        if threshold is not None:
            records, total = client.similarity_search(
                args["smiles"], int(threshold), max_records=SEARCH_WALK_CAP)
        else:
            records, total = client.substructure_search(
                args["smiles"], max_records=SEARCH_WALK_CAP)
            # substructure_search only ID-sorts the full walk; sort the
            # capped set too so presentation stays deterministic.
            records = sorted(
                records, key=lambda r: r.get("molecule_chembl_id") or "")
        walk_truncated = total is not None and total > len(records)
        if max_phase is not None:
            # Client-side like the name branch: the searchers own their
            # query params, and filtered totals must count what the filter
            # kept, not the unfiltered upstream total.
            records = [m for m in records
                       if m.get("max_phase") is not None
                       and float(m["max_phase"]) == float(max_phase)]
        resp = marshal.compound_search_response(records[:limit], len(records))
        if walk_truncated:
            # Additive disclosure: ranking/filtering was scoped to the
            # first SEARCH_WALK_CAP records walked, not the full upstream
            # match set (whose size is upstream_total).
            resp["walk_truncated"] = True
            resp["upstream_total"] = total
        return marshal.compact_json(resp)

    # Name search: synonym substring match (the original's formulation —
    # reproduces its result sets, e.g. "aspirin" -> 8 molecules), with a
    # pref_name fallback for molecules that have no synonym rows.
    params = {"molecule_synonyms__molecule_synonym__icontains": args["name"]}
    if max_phase is not None:
        params["max_phase"] = max_phase
    records, total = client.paginate("/molecule.json", "molecules", params,
                                     max_records=limit)
    if not records:
        params = {"pref_name__icontains": args["name"]}
        if max_phase is not None:
            params["max_phase"] = max_phase
        records, total = client.paginate("/molecule.json", "molecules", params,
                                         max_records=limit)
    return marshal.compact_json(marshal.compound_search_response(records, total))


# ── drug_search ──────────────────────────────────────────────────────────────

def drug_search(args: dict) -> str:
    limit = _limit(args)
    client = _drugs()
    # Post-filters need the full molecule join; without them, joining only
    # the first page of parents avoids an unbounded N+1 fan-out on broad
    # indications ("cancer": thousands of parents → 80-150+ serially
    # throttled EBI calls → -32001 timeout). Review 3377922588.
    post_filtered = bool(
        args.get("molecule_chembl_id") or args.get("drug_name")
        or args.get("max_phase") is not None)
    res = client.search_drugs_by_indication(
        args["indication"], only_approved=bool(args.get("only_approved")),
        max_drugs=None if post_filtered else limit)
    drugs = res["drugs"]

    if args.get("molecule_chembl_id"):
        drugs = [d for d in drugs
                 if d["parent_molecule_chembl_id"] == args["molecule_chembl_id"]]
    if args.get("drug_name"):
        needle = args["drug_name"].lower()
        drugs = [d for d in drugs if needle in (d.get("pref_name") or "").lower()]
    if args.get("max_phase") is not None:
        wanted = float(args["max_phase"])
        drugs = [d for d in drugs
                 if d.get("max_phase") is not None
                 and float(d["max_phase"]) >= wanted]

    total = len(drugs) if post_filtered else res["total_parents"]
    page = drugs[:limit]
    # Join by chembl_id, NOT zip-by-position (review 3387178867 / bench
    # 3389709159): with missing_ok a dropped molecule record would shift
    # every subsequent zip pairing — the misalignment trap. A referential
    # gap degrades that one drug to molecule={} (same tolerance the
    # client-side join already has at search_drugs_by_indication).
    mol_by_id = {
        m["molecule_chembl_id"]: m
        for m in (client.get_molecules(
            [d["parent_molecule_chembl_id"] for d in page],
            missing_ok=True) if page else [])
    }
    pairs = [(mol_by_id.get(d["parent_molecule_chembl_id"], {}), d)
             for d in page]
    return marshal.compact_json(marshal.drug_search_response(
        pairs, total,
        indication_query=res["indication_query"],
        total_indication_rows=res["total_indication_rows"]))


# ── get_admet ────────────────────────────────────────────────────────────────

def get_admet(args: dict) -> str:
    mol_id = args["molecule_chembl_id"]
    # NOTE (review 3387178867 adjudication): this is the chembl_bioactivity
    # client, whose get_molecules is tolerant (returns found records only,
    # no MoleculeNotFoundError — that raise belongs to the chembl_drug_search
    # client used elsewhere). The `records[0] if records else None` fallback
    # below is therefore LIVE, not dead: an unknown id yields the marshal's
    # found:false arm.
    records = _bio().get_molecules([mol_id])
    return marshal.compact_json(
        marshal.admet_response(records[0] if records else None, mol_id))


# ── get_bioactivity ──────────────────────────────────────────────────────────

def get_bioactivity(args: dict) -> str:
    limit = _limit(args)
    params: dict = {}
    if args.get("molecule_chembl_id"):
        params["molecule_chembl_id"] = args["molecule_chembl_id"]
    if args.get("target_chembl_id"):
        params["target_chembl_id"] = args["target_chembl_id"]
    if args.get("activity_type"):
        params["standard_type"] = args["activity_type"]
    if args.get("min_pchembl") is not None:
        params["pchembl_value__gte"] = args["min_pchembl"]
    if args.get("min_value") is not None:
        params["standard_value__gte"] = args["min_value"]
    if args.get("max_value") is not None:
        params["standard_value__lte"] = args["max_value"]
    if args.get("unit"):
        params["standard_units"] = args["unit"]
    activities, total = _single_page(_bio(), "activity", params, limit)
    return marshal.compact_json(marshal.bioactivity_response(activities, total))


# ── get_mechanism ────────────────────────────────────────────────────────────

def get_mechanism(args: dict) -> str:
    limit = _limit(args)
    params: dict = {}
    if args.get("target_chembl_id"):
        params["target_chembl_id"] = args["target_chembl_id"]
    if args.get("action_type"):
        params["action_type"] = args["action_type"]
    mol_id = args.get("molecule_chembl_id")
    if mol_id:
        params["molecule_chembl_id"] = mol_id
    mechanisms, total = _single_page(_bio(), "mechanism", params, limit)
    if not mechanisms and mol_id:
        # Mechanisms may be stored under the salt form; retry matching the
        # parent so parent compound IDs work (as the original documented).
        params.pop("molecule_chembl_id")
        params["parent_molecule_chembl_id"] = mol_id
        mechanisms, total = _single_page(_bio(), "mechanism", params, limit)
    return marshal.compact_json(marshal.mechanism_response(mechanisms, total))


# ── target_search ────────────────────────────────────────────────────────────

def target_search(args: dict) -> str:
    limit = _limit(args)
    params: dict = {}
    if args.get("target_chembl_id"):
        params["target_chembl_id"] = args["target_chembl_id"]
    if args.get("gene_symbol"):
        params["target_components__target_component_synonyms__"
               "component_synonym__iexact"] = args["gene_symbol"]
    if args.get("target_name"):
        params["pref_name__icontains"] = args["target_name"]
    if args.get("organism"):
        params["organism__icontains"] = args["organism"]
    if args.get("target_type"):
        params["target_type"] = args["target_type"]
    records, total = _targets().paginate("target", params, max_records=limit)
    return marshal.compact_json(marshal.target_search_response(records, total))


HANDLERS = {
    "compound_search": compound_search,
    "drug_search": drug_search,
    "get_admet": get_admet,
    "get_bioactivity": get_bioactivity,
    "get_mechanism": get_mechanism,
    "target_search": target_search,
}


def build_server() -> Tier1Server:
    return Tier1Server("chembl-mcp-server", load_schemas(__package__), HANDLERS)


def main() -> None:
    # Standalone serving gate (see mcp_servers_common/gate.py): enforce
    # mcp_bio/deferred.json exactly like the aggregate. Serve-time only —
    # build_server() stays pristine for parity tests and the aggregate.
    t1 = build_server()
    apply_gate_tier1(t1)
    t1.run()


if __name__ == "__main__":
    main()
