"""Minimal CLI: print structured JSON for a lookup or a related-terms retrieval.

Examples
--------
python -m ols_terms lookup go GO:0006281
python -m ols_terms descendants efo EFO:0005105
python -m ols_terms ancestors uberon UBERON:0002107 --hierarchical
"""

from __future__ import annotations

import argparse
import json
import sys

from .api import get_ancestors, get_descendants, lookup_term
from .client import OLSClient
from .records import canonical_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ols_terms")
    parser.add_argument("command", choices=["lookup", "descendants", "ancestors"])
    parser.add_argument("ontology", help="OLS ontology id, e.g. efo, mondo, go, uberon")
    parser.add_argument("term_id", help="CURIE (GO:0006281) or full IRI")
    parser.add_argument("--hierarchical", action="store_true",
                        help="use hierarchical* relations (is_a + part_of etc.)")
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--include-parents", action="store_true",
                        help="also fetch direct parents for every related term (1 extra request per term)")
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args(argv)

    kwargs = {} if args.base_url is None else {"base_url": args.base_url}
    client = OLSClient(**kwargs)

    if args.command == "lookup":
        rec = lookup_term(client, args.ontology, args.term_id)
        out = rec.to_dict()
    else:
        fn = get_descendants if args.command == "descendants" else get_ancestors
        res = fn(
            client,
            args.ontology,
            args.term_id,
            hierarchical=args.hierarchical,
            page_size=args.page_size,
            include_parents=args.include_parents,
        )
        out = res.to_dict()
    print(json.dumps(json.loads(canonical_json(out)), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
