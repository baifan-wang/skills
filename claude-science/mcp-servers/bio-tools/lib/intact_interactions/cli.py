"""Command-line interface: query -> JSON on stdout.

Example
-------
python -m intact_interactions P04637 --min-mi-score 0.45 > tp53_interactions.json
"""

from __future__ import annotations

import argparse
import json
import sys

from .client import IntActClient
from .core import DEFAULT_PAGE_SIZE, fetch_interactions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="intact-interactions",
        description=(
            "Retrieve all binary interactions for a protein/gene query from "
            "the IntAct web service, with MI-score filtering and full pagination."
        ),
    )
    parser.add_argument("query", help="UniProt accession, gene name, or IntAct AC")
    parser.add_argument("--min-mi-score", type=float, default=0.0)
    parser.add_argument("--max-mi-score", type=float, default=1.0)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument(
        "--species",
        action="append",
        default=None,
        help="Interactor species filter (repeatable), e.g. 'Homo sapiens'",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indent (0 = compact)")
    args = parser.parse_args(argv)

    with IntActClient() as client:
        result = fetch_interactions(
            args.query,
            min_mi_score=args.min_mi_score,
            max_mi_score=args.max_mi_score,
            page_size=args.page_size,
            interactor_species=args.species,
            client=client,
        )
    json.dump(result, sys.stdout, indent=args.indent or None, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
