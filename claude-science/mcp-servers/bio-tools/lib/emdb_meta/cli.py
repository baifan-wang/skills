"""Command-line interface: emdb-meta entries / search / battery."""
from __future__ import annotations

import argparse
import json
import sys

from .client import EMDBClient
from .records import fetch_entry_records
from .search import run_search_spec, DEFAULT_FL


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="emdb-meta",
        description="Structured EM map metadata from the EMDB REST API (entries + search; never downloads map volumes).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_entries = sub.add_parser("entries", help="Fetch structured records for EMD accessions")
    p_entries.add_argument("ids", nargs="+", help="EMD accessions (EMD-1234 or 1234)")

    p_search = sub.add_parser("search", help="Run a search query to completion with count verification")
    p_search.add_argument("query", help='e.g. \'title:"apoferritin" AND resolution:[0 TO 1.5]\'')
    p_search.add_argument("--fl", default=DEFAULT_FL, help="comma-separated result fields")

    p_batt = sub.add_parser("battery", help="Run a battery JSON file (entries + search specs)")
    p_batt.add_argument("battery_json", help="path to battery.json")

    args = parser.parse_args(argv)
    client = EMDBClient()

    if args.command == "entries":
        out = fetch_entry_records(client, args.ids)
    elif args.command == "search":
        out = run_search_spec(client, args.query, fl=args.fl)
    else:
        battery = json.load(open(args.battery_json))
        out = {
            "entries": fetch_entry_records(client, battery["entry_ids"]),
            "searches": [run_search_spec(client, spec["query"]) for spec in battery["search_specs"]],
        }
    json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
