"""Minimal CLI: python -m gtex_expression <method> [json-kwargs]

Examples:
  python -m gtex_expression tissue_sites
  python -m gtex_expression expression_summary '{"gene": "GAPDH"}'
  python -m gtex_expression eqtl_genes '{"tissue_site_detail_id": "Pancreas"}'
"""
import json
import sys

from .tool import GtexExpression

METHODS = ["tissue_sites", "dataset_info", "sample_info", "resolve_genes",
           "median_expression", "expression_summary", "gene_expression",
           "top_expressed", "eqtl_genes", "single_tissue_eqtls",
           "multi_tissue_eqtls", "calculate_eqtl"]


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help") or argv[0] not in METHODS:
        print(__doc__)
        print("methods:", ", ".join(METHODS))
        return 1 if argv and argv[0] not in ("-h", "--help") else 0
    method = argv[0]
    kwargs = json.loads(argv[1]) if len(argv) > 1 else {}
    dataset_id = kwargs.pop("dataset_id", None)
    tool = GtexExpression(**({"dataset_id": dataset_id} if dataset_id else {}))
    out = getattr(tool, method)(**kwargs)
    json.dump(out, sys.stdout, indent=2, sort_keys=True, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
