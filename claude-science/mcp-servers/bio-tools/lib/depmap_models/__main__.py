"""CLI: python -m depmap_models <command> [args]

Commands:
  list [--tissue T] [--cancer-type C]
  get <SIDM-id-or-name>
  search <query>
  deps <gene-symbol> [--model SIDMxxxxx]
  genes <query> [--exact]
"""

from __future__ import annotations

import argparse
import json
import sys

from .tool import DepMapModels


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="depmap_models")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list")
    sp.add_argument("--tissue")
    sp.add_argument("--cancer-type")

    sp = sub.add_parser("get")
    sp.add_argument("ident")

    sp = sub.add_parser("search")
    sp.add_argument("query")

    sp = sub.add_parser("deps")
    sp.add_argument("gene")
    sp.add_argument("--model")

    sp = sub.add_parser("genes")
    sp.add_argument("query")
    sp.add_argument("--exact", action="store_true")

    a = p.parse_args(argv)
    t = DepMapModels()
    if a.cmd == "list":
        out = t.list_models(tissue=a.tissue, cancer_type=a.cancer_type)
    elif a.cmd == "get":
        out = t.get_model(a.ident)
    elif a.cmd == "search":
        out = t.search_models(a.query)
    elif a.cmd == "deps":
        out = t.gene_dependencies(a.gene, model_id=a.model)
    else:
        out = t.search_genes(a.query, exact=a.exact)
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
