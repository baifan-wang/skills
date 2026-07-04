"""CLI: python -m cadd_scores {variant|position|range} ..."""
from __future__ import annotations

import argparse
import json
import sys

from .tool import CaddScores, DEFAULT_VERSION


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="cadd_scores",
                                description="CADD deleteriousness scores (REST)")
    p.add_argument("--version-string", default=DEFAULT_VERSION,
                   help="CADD release incl. build, e.g. GRCh38-v1.7 (default) "
                        "or GRCh37-v1.6")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("variant", help="score one SNV")
    v.add_argument("chrom"); v.add_argument("pos", type=int)
    v.add_argument("ref"); v.add_argument("alt")

    q = sub.add_parser("position", help="all substitutions at a position")
    q.add_argument("chrom"); q.add_argument("pos", type=int)

    r = sub.add_parser("range", help="all SNVs in a range (<=100 bp)")
    r.add_argument("chrom"); r.add_argument("start", type=int)
    r.add_argument("end", type=int)

    a = p.parse_args(argv)
    tool = CaddScores()
    if a.cmd == "variant":
        out = tool.variant_score(a.chrom, a.pos, a.ref, a.alt, version=a.version_string)
    elif a.cmd == "position":
        out = tool.position_scores(a.chrom, a.pos, version=a.version_string)
    else:
        out = tool.range_scores(a.chrom, a.start, a.end, version=a.version_string)
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
