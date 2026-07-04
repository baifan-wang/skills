"""Command-line interface: python -m string_network --genes TP53,BRCA1,... [options]"""

from __future__ import annotations

import argparse
import json
import sys

from .client import DEFAULT_BASE_URL, DEFAULT_CALLER_IDENTITY, StringClient
from .core import build_network


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="string-network",
        description="Retrieve a STRING interaction network for a list of gene symbols.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--genes", help="comma-separated gene symbols")
    group.add_argument("--genes-file", help="file with one gene symbol per line")
    parser.add_argument("--species", type=int, default=9606, help="NCBI taxon ID (default 9606)")
    parser.add_argument(
        "--required-score", type=int, default=700,
        help="minimum combined score 0-1000 (default 700)",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--caller-identity", default=DEFAULT_CALLER_IDENTITY)
    parser.add_argument("-o", "--output", default="-", help="output JSON path (default stdout)")
    parser.add_argument(
        "--no-request-log", action="store_true",
        help="omit the per-request provenance log from the output",
    )
    args = parser.parse_args(argv)

    if args.genes:
        symbols = [s.strip() for s in args.genes.split(",") if s.strip()]
    else:
        with open(args.genes_file, encoding="utf-8") as fh:
            symbols = [line.strip() for line in fh if line.strip()]

    client = StringClient(base_url=args.base_url, caller_identity=args.caller_identity)
    result = build_network(
        symbols,
        species=args.species,
        required_score=args.required_score,
        client=client,
        include_request_log=not args.no_request_log,
    )
    text = json.dumps(result, indent=2)
    if args.output == "-":
        print(text)
    else:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
