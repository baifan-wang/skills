"""CLI: python -m openfda_labels --brand-name Tylenol --sections indications_and_usage"""

from __future__ import annotations

import argparse
import json
import sys

from .client import OpenFDAClient
from .runner import run_spec


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="openfda-labels",
        description="Complete, deterministic retrieval of FDA drug labels from api.fda.gov",
    )
    p.add_argument("--active-ingredient", help="openfda.substance_name phrase")
    p.add_argument("--generic-name", help="openfda.generic_name phrase")
    p.add_argument("--brand-name", help="openfda.brand_name phrase")
    p.add_argument("--route", help="openfda.route phrase, e.g. ORAL, TRANSDERMAL")
    p.add_argument("--product-type", help='"HUMAN PRESCRIPTION DRUG" or "HUMAN OTC DRUG"')
    p.add_argument("--search", help="raw openFDA search string (overrides mapped fields)")
    p.add_argument("--exact", action="store_true", help="use .exact (non-analyzed) field variants")
    p.add_argument("--sections", help="comma-separated label sections for targeted extraction "
                                      "(e.g. indications_and_usage,boxed_warning)")
    p.add_argument("--api-key", default=None, help="openFDA API key (optional)")
    p.add_argument("--page-size", type=int, default=1000)
    p.add_argument("--output", default="-", help="output path for JSON result (default stdout)")
    args = p.parse_args(argv)

    spec: dict = {}
    for cli_key, spec_key in [
        ("active_ingredient", "active_ingredient"),
        ("generic_name", "generic_name"),
        ("brand_name", "brand_name"),
        ("route", "route"),
        ("product_type", "product_type"),
        ("search", "search"),
    ]:
        value = getattr(args, cli_key)
        if value:
            spec[spec_key] = value
    if args.exact:
        spec["exact"] = True

    sections = [s.strip() for s in args.sections.split(",")] if args.sections else None

    with OpenFDAClient(api_key=args.api_key, page_size=args.page_size) as client:
        result = run_spec(spec, client, sections=sections)

    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output == "-":
        print(payload)
    else:
        with open(args.output, "w") as fh:
            fh.write(payload)
        print(f"wrote {args.output}: {result['count']} of {result['total']} records",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
