"""CLI: python -m clingen_curations <method> [args].

Examples:
  python -m clingen_curations gene_validity --gene BRCA1
  python -m clingen_curations dosage_sensitivity --gene MECP2
  python -m clingen_curations actionability --gene BRCA1 --context both
  python -m clingen_curations variant_classifications --gene PAH
"""
import argparse
import json
import sys

from .tool import ClinGenCurations


def main(argv=None):
    p = argparse.ArgumentParser(prog="clingen_curations")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("gene_validity")
    s.add_argument("--gene")

    s = sub.add_parser("dosage_sensitivity")
    s.add_argument("--gene")
    s.add_argument("--include-regions", action="store_true")

    s = sub.add_parser("actionability")
    s.add_argument("--gene")
    s.add_argument("--context", default="both",
                   choices=["adult", "pediatric", "both"])

    s = sub.add_parser("variant_classifications")
    s.add_argument("--gene")
    s.add_argument("--caid")
    s.add_argument("--hgvs")

    a = p.parse_args(argv)
    tool = ClinGenCurations()
    if a.cmd == "gene_validity":
        out = tool.gene_validity(gene=a.gene)
    elif a.cmd == "dosage_sensitivity":
        out = tool.dosage_sensitivity(gene=a.gene, include_regions=a.include_regions)
    elif a.cmd == "actionability":
        out = tool.actionability(gene=a.gene, context=a.context)
    else:
        out = tool.variant_classifications(gene=a.gene, caid=a.caid, hgvs=a.hgvs)
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
