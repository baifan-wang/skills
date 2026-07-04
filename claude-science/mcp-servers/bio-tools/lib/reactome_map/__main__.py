"""Command-line interface: ``python -m reactome_map TP53 BRCA1 --id-type symbol``."""
from __future__ import annotations

import argparse
import json
import sys

from .mapper import compact_view, map_identifiers


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="reactome-map",
        description="Map gene symbols or UniProt accessions to Reactome pathways "
        "(AnalysisService token workflow + ContentService version stamp).",
    )
    ap.add_argument("identifiers", nargs="+", help="gene symbols or UniProt accessions")
    ap.add_argument(
        "--id-type", choices=["symbol", "uniprot"], default="symbol",
        help="type of the supplied identifiers (default: symbol)",
    )
    ap.add_argument("--species", default="Homo sapiens", help="species filter (default: Homo sapiens)")
    ap.add_argument("--no-disease", action="store_true", help="exclude disease pathways")
    ap.add_argument(
        "--resource", default="TOTAL",
        help="AnalysisService molecule-resource view (TOTAL, UNIPROT, ENSEMBL, ...; default TOTAL)",
    )
    ap.add_argument(
        "--format", choices=["compact", "full"], default="compact",
        help="compact = per-gene low-level pathways (stId, name, species); "
        "full = complete result incl. statistics, batch summary and provenance",
    )
    ap.add_argument("--out", default="-", help="output JSON file (default: stdout)")
    args = ap.parse_args(argv)

    result = map_identifiers(
        args.identifiers,
        args.id_type,
        species=args.species,
        include_disease=not args.no_disease,
        resource=args.resource,
    )
    if args.format == "compact":
        result = compact_view(result)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out == "-":
        print(text)
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
