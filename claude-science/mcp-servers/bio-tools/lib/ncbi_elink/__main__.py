"""Minimal CLI: python -m ncbi_elink links gene pubmed 7157 672 [--linkname gene_pubmed]
                python -m ncbi_elink linknames gene --db pubmed"""
import argparse
import json
import sys

from .elink import elink_links, enumerate_linknames


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="ncbi_elink",
                                description="Structured NCBI elink cross-database links (per-UID, by linkname)")
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("links", help="per-UID cross-database links")
    pl.add_argument("dbfrom")
    pl.add_argument("db")
    pl.add_argument("uids", nargs="+")
    pl.add_argument("--linkname", default=None)
    pe = sub.add_parser("linknames", help="enumerate available link names from a source db")
    pe.add_argument("dbfrom")
    pe.add_argument("--db", default=None)
    args = p.parse_args(argv)
    if args.cmd == "links":
        out = elink_links(args.dbfrom, args.db, args.uids, linkname=args.linkname)
    else:
        out = enumerate_linknames(args.dbfrom, db=args.db)
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
