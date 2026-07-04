"""CLI: python -m interpro_domains ACC [ACC ...] [--text|--pretty] [--page-size N] [-o out.json]

Default output is compact JSON (the machine-readable mode an agent ingests);
--pretty emits indented JSON, --text emits the tab-separated architecture table.
"""

from __future__ import annotations

import argparse
import json
import sys

from .client import fetch_domain_architecture
from .summary import summary_to_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="interpro_domains",
        description="Fetch complete InterPro domain architectures for UniProt accessions.",
    )
    parser.add_argument("accessions", nargs="+", help="UniProt accessions (e.g. P04637 Q8WZ42)")
    parser.add_argument("--page-size", type=int, default=200, help="API page size (default 200)")
    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument("--text", action="store_true",
                     help="emit the tab-separated architecture table (human mode)")
    fmt.add_argument("--pretty", action="store_true", help="emit indented JSON instead of compact JSON")
    parser.add_argument("-o", "--output", default=None, help="write output to a file instead of stdout")
    args = parser.parse_args(argv)

    result = fetch_domain_architecture(args.accessions, page_size=args.page_size)
    summaries = result["summaries"]

    if args.text:
        out = "\n".join(summary_to_text(summaries[acc]) for acc in args.accessions)
    elif args.pretty:
        out = json.dumps({acc: summaries[acc] for acc in args.accessions}, indent=2, sort_keys=False)
    else:
        out = json.dumps({acc: summaries[acc] for acc in args.accessions},
                         separators=(",", ":"), sort_keys=False)

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out + ("\n" if not out.endswith("\n") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
