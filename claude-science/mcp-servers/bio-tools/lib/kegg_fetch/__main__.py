"""CLI: python -m kegg_fetch hsa:7157 hsa04110 C00031 [--json|--flat] [-o DIR]"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .client import KeggClient


def safe_name(entry_id: str) -> str:
    return entry_id.replace(":", "_")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kegg_fetch", description="Batched KEGG REST retrieval (10 entries per request)."
    )
    parser.add_argument("ids", nargs="+", help="KEGG entry ids, e.g. hsa:7157 hsa04110 C00031")
    parser.add_argument("--format", choices=["json", "flat"], default="json",
                        help="stdout format when -o is not given (default: json)")
    parser.add_argument("-o", "--outdir", default=None,
                        help="write per-entry <id>.txt and <id>.json files to this directory")
    args = parser.parse_args(argv)

    client = KeggClient()
    entries = client.get_entries(args.ids)

    if args.outdir:
        outdir = pathlib.Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        for e in entries:
            (outdir / f"{safe_name(e.requested_id)}.txt").write_text(e.raw)
            (outdir / f"{safe_name(e.requested_id)}.json").write_text(
                json.dumps(e.record, indent=2, sort_keys=True) + "\n"
            )
        print(f"wrote {len(entries)} entries to {outdir} "
              f"({client.stats.http_requests} HTTP requests)", file=sys.stderr)
    elif args.format == "flat":
        sys.stdout.write("".join(e.raw for e in entries))
    else:
        json.dump([e.record for e in entries], sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
