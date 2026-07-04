"""Minimal CLI: python -m panglaodb_markers <command> [args].

Commands:
  options                      enumerate species / organs / cell types
  markers [--cell-type CT] [--organ O] [--species Hs|Mm]
          [--sensitivity-min X] [--specificity-max X] [--canonical-only]
  gene SYMBOL [--synonyms]     reverse lookup: cell types for a gene
"""
import argparse
import json
import sys

from .core import PanglaoDB


def main(argv=None):
    p = argparse.ArgumentParser(prog="panglaodb_markers")
    p.add_argument("--tsv", default=None, help="path to a local marker .tsv.gz (offline)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("options")

    m = sub.add_parser("markers")
    m.add_argument("--cell-type")
    m.add_argument("--organ")
    m.add_argument("--species", choices=["Hs", "Mm"])
    m.add_argument("--sensitivity-min", type=float)
    m.add_argument("--specificity-max", type=float)
    m.add_argument("--canonical-only", action="store_true")

    g = sub.add_parser("gene")
    g.add_argument("symbol")
    g.add_argument("--synonyms", action="store_true")

    args = p.parse_args(argv)
    db = PanglaoDB(args.tsv)
    if args.cmd == "options":
        out = db.options()
    elif args.cmd == "markers":
        out = db.marker_genes(
            cell_type=args.cell_type,
            organ=args.organ,
            species=args.species,
            sensitivity_min=args.sensitivity_min,
            specificity_max=args.specificity_max,
            canonical_only=args.canonical_only,
        )
    else:
        out = db.cell_types_for_gene(args.symbol, include_synonyms=args.synonyms)
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
