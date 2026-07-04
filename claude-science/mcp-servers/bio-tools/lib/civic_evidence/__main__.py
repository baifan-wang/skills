"""CLI: python -m civic_evidence <method> [args...] -> JSON on stdout.

Examples
--------
python -m civic_evidence search_genes BRAF
python -m civic_evidence gene_variants 5
python -m civic_evidence get_variant 12
python -m civic_evidence search_variants V600E --gene-id 5
python -m civic_evidence get_evidence_item 1409
python -m civic_evidence search_evidence --filter evidence_level=A --filter status=ACCEPTED
python -m civic_evidence get_assertion 7
python -m civic_evidence search_assertions --filter disease_name=Melanoma
python -m civic_evidence get_molecular_profile 12
python -m civic_evidence search_molecular_profiles "BRAF V600E"
python -m civic_evidence search_diseases Melanoma
python -m civic_evidence search_therapies Vemurafenib
"""
import argparse
import json
import sys

from .tool import CivicEvidence

INT_FILTERS = {"evidence_rating", "molecular_profile_id", "variant_id",
               "disease_id", "therapy_id", "phenotype_id", "source_id",
               "assertion_id", "evidence_id"}


def parse_filters(pairs):
    filters = {}
    for p in pairs or []:
        if "=" not in p:
            raise SystemExit(f"--filter expects key=value, got {p!r}")
        k, v = p.split("=", 1)
        filters[k] = int(v) if k in INT_FILTERS else v
    return filters


def main(argv=None):
    ap = argparse.ArgumentParser(prog="civic_evidence")
    ap.add_argument("method", choices=[
        "search_genes", "gene_variants", "get_variant", "search_variants",
        "get_evidence_item", "search_evidence", "get_assertion",
        "search_assertions", "get_molecular_profile",
        "search_molecular_profiles", "search_diseases", "search_therapies"])
    ap.add_argument("arg", nargs="?", help="symbol / name / numeric id")
    ap.add_argument("--gene-id", type=int, default=None)
    ap.add_argument("--filter", action="append", metavar="KEY=VALUE",
                    help="repeatable; for search_evidence / search_assertions")
    args = ap.parse_args(argv)

    tool = CivicEvidence()
    m = args.method
    if m in ("search_evidence", "search_assertions"):
        out = getattr(tool, m)(**parse_filters(args.filter))
    elif m in ("gene_variants", "get_variant", "get_evidence_item",
               "get_assertion", "get_molecular_profile"):
        if args.arg is None:
            raise SystemExit(f"{m} requires a numeric id argument")
        out = getattr(tool, m)(int(args.arg))
    elif m == "search_variants":
        if args.arg is None:
            raise SystemExit("search_variants requires a name argument")
        out = tool.search_variants(args.arg, args.gene_id)
    else:
        if args.arg is None:
            raise SystemExit(f"{m} requires a string argument")
        out = getattr(tool, m)(args.arg)
    json.dump(out, sys.stdout, indent=2, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
