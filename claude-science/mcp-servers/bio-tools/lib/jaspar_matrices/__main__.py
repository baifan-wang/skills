"""CLI: python -m jaspar_matrices <command> [args]"""
from __future__ import annotations

import argparse
import json
import sys

from . import (JasparClient, get_matrix, matrix_versions, list_matrices,
               list_species, list_taxa, list_collections, list_releases)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="jaspar-matrices")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("matrix"); sp.add_argument("matrix_id")
    sp = sub.add_parser("versions"); sp.add_argument("base_id")
    sp = sub.add_parser("list")
    for flag in ("--collection", "--tax-group", "--tax-id", "--name", "--search", "--version"):
        sp.add_argument(flag)
    for cmd in ("species", "taxa", "collections", "releases"):
        sub.add_parser(cmd)
    a = p.parse_args(argv)
    c = JasparClient()
    if a.cmd == "matrix":
        out = get_matrix(c, a.matrix_id)
    elif a.cmd == "versions":
        out = matrix_versions(c, a.base_id)
    elif a.cmd == "list":
        out = list_matrices(c, collection=a.collection, tax_group=a.tax_group,
                            tax_id=a.tax_id, name=a.name, search=a.search,
                            version=a.version)
    elif a.cmd == "species":
        out = list_species(c)
    elif a.cmd == "taxa":
        out = list_taxa(c)
    elif a.cmd == "collections":
        out = list_collections(c)
    else:
        out = list_releases(c)
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
