"""CLI: ``python -m uniprot_fetch ACC1 ACC2 ... [--formats fasta,txt] [--outdir DIR]``."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import UniProtClient


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="uniprot-fetch",
        description="Batched UniProtKB retrieval (FASTA + flat-file), split back per accession.",
    )
    p.add_argument(
        "accessions",
        nargs="+",
        help="UniProtKB accessions, or @file with one accession per line",
    )
    p.add_argument("--formats", default="fasta,txt", help="comma-separated: fasta,txt (default both)")
    p.add_argument("--outdir", default="uniprot_out", help="output directory (per-format subdirs)")
    args = p.parse_args(argv)

    accs: list[str] = []
    for a in args.accessions:
        if a.startswith("@"):
            accs.extend(ln.strip() for ln in Path(a[1:]).read_text().splitlines() if ln.strip())
        else:
            accs.append(a)

    client = UniProtClient()
    manifest = client.fetch_all(accs, outdir=args.outdir, formats=tuple(args.formats.split(",")))
    summary = {
        "n_accessions": len(accs),
        "missing": manifest["missing"],
        "http_requests": manifest["http"]["requests"],
        "bytes_downloaded": manifest["http"]["bytes_downloaded"],
        "outdir": args.outdir,
    }
    json.dump(summary, sys.stdout, indent=2)
    print()
    return 1 if any(manifest["missing"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
