"""CLI: python -m encode_search <command> ...

Commands:
  experiment ENCSR...     get_experiment
  file ENCFF...           get_file
  biosample ENCBS...      get_biosample
  search-experiments --assay-title T --target X --organism O --before YYYY-MM-DD
"""
import argparse
import json
import sys

from .tool import EncodeSearch


def main(argv=None):
    p = argparse.ArgumentParser(prog="encode_search")
    sub = p.add_subparsers(dest="cmd", required=True)
    for cmd in ("experiment", "file", "biosample"):
        sp = sub.add_parser(cmd)
        sp.add_argument("accession")
    se = sub.add_parser("search-experiments")
    se.add_argument("--assay-title")
    se.add_argument("--target")
    se.add_argument("--organism")
    se.add_argument("--before", help="date_released upper cutoff YYYY-MM-DD")
    args = p.parse_args(argv)

    tool = EncodeSearch()
    if args.cmd == "experiment":
        out = tool.get_experiment(args.accession)
    elif args.cmd == "file":
        out = tool.get_file(args.accession)
    elif args.cmd == "biosample":
        out = tool.get_biosample(args.accession)
    else:
        out = tool.search_experiments(assay_title=args.assay_title,
                                      target=args.target, organism=args.organism,
                                      date_released_before=args.before)
        out = {"total": out["total"], "accessions": out["accessions"]}
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
