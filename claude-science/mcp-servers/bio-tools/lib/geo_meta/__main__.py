"""CLI: ``python -m geo_meta GSE52778 [GSE63310 ...]`` or ``python -m geo_meta --search '<term>'``.

Prints structured JSON (sorted keys) to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys

from .client import PoliteClient
from .core import fetch_series_batch, search_series


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geo_meta", description=__doc__)
    parser.add_argument("accessions", nargs="*", help="GSE accessions, e.g. GSE52778 GSE63310")
    parser.add_argument("--search", help="GEO DataSets (db=gds) search term instead of accessions")
    parser.add_argument("--retmax", type=int, default=500, help="max search records (default 500)")
    args = parser.parse_args(argv)

    if bool(args.accessions) == bool(args.search):
        parser.error("provide either GSE accessions or --search '<term>', not both/neither")

    with PoliteClient() as client:
        if args.search:
            result = search_series(args.search, client=client, retmax=args.retmax)
        else:
            result = fetch_series_batch(args.accessions, client=client)
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
