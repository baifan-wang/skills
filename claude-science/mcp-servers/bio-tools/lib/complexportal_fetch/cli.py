"""Command-line interface.

Examples
--------
python -m complexportal_fetch get CPX-2158 CPX-663 --format tsv
python -m complexportal_fetch search P04637 --format json
"""
from __future__ import annotations

import argparse
import sys

from .client import ComplexPortalClient
from .fetch import fetch_complexes, search_by_participant
from .table import records_to_tsv, search_to_tsv, records_to_json


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="complexportal-fetch")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="fetch complexes by CPX accession")
    g.add_argument("accessions", nargs="+", metavar="CPX-AC")
    g.add_argument("--format", choices=["json", "tsv", "tsv-complex"], default="json")

    s = sub.add_parser("search", help="search complexes by participant accession")
    s.add_argument("accessions", nargs="+", metavar="UNIPROT_AC")
    s.add_argument("--format", choices=["json", "tsv"], default="json")
    s.add_argument("--page-size", type=int, default=50)
    s.add_argument("--free-text", action="store_true",
                   help="bare free-text query instead of participant-restricted pxref: query")

    args = ap.parse_args(argv)
    with ComplexPortalClient() as client:
        if args.cmd == "get":
            out = fetch_complexes(args.accessions, client=client)
            if out["not_found"]:
                print(f"WARNING: not found: {', '.join(out['not_found'])}", file=sys.stderr)
            if args.format == "json":
                print(records_to_json(out["records"], indent=2))
            elif args.format == "tsv":
                sys.stdout.write(records_to_tsv(out["records"], level="participant"))
            else:
                sys.stdout.write(records_to_tsv(out["records"], level="complex"))
        else:
            results = [
                search_by_participant(ac, client=client, page_size=args.page_size,
                                      participants_only=not args.free_text)
                for ac in args.accessions
            ]
            if args.format == "json":
                print(records_to_json(results, indent=2))
            else:
                sys.stdout.write(search_to_tsv(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
