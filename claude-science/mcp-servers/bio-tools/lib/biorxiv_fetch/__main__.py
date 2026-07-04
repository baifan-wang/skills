"""CLI: python -m biorxiv_fetch <command> ... (prints JSON to stdout)."""
from __future__ import annotations

import argparse
import json
import sys

from .tool import BiorxivFetch


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="biorxiv_fetch")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("preprint", help="all versions of one DOI")
    s.add_argument("doi")
    s.add_argument("--server", default="biorxiv", choices=("biorxiv", "medrxiv"))

    s = sub.add_parser("list", help="complete interval listing")
    s.add_argument("server", choices=("biorxiv", "medrxiv"))
    s.add_argument("date_from")
    s.add_argument("date_to")
    s.add_argument("--category")

    s = sub.add_parser("published", help="preprint->journal links")
    s.add_argument("server", choices=("biorxiv", "medrxiv"))
    s.add_argument("date_from")
    s.add_argument("date_to")
    s.add_argument("--publisher-prefix")

    s = sub.add_parser("funder", help="preprints by funder ROR id")
    s.add_argument("ror_id")
    s.add_argument("date_from")
    s.add_argument("date_to")
    s.add_argument("--server", default="biorxiv", choices=("biorxiv", "medrxiv"))

    s = sub.add_parser("content-stats", help="bioRxiv content statistics")
    s.add_argument("--interval", default="m", choices=("m", "y"))
    s.add_argument("--through")

    s = sub.add_parser("usage-stats", help="bioRxiv usage statistics")
    s.add_argument("--interval", default="m", choices=("m", "y"))
    s.add_argument("--through")

    a = p.parse_args(argv)
    tool = BiorxivFetch()
    if a.cmd == "preprint":
        out = tool.get_preprint(a.doi, server=a.server)
    elif a.cmd == "list":
        out = tool.list_preprints(a.server, a.date_from, a.date_to, category=a.category)
    elif a.cmd == "published":
        out = tool.published_links(a.server, a.date_from, a.date_to,
                                   publisher_prefix=a.publisher_prefix)
    elif a.cmd == "funder":
        out = tool.by_funder(a.ror_id, a.date_from, a.date_to, server=a.server)
    elif a.cmd == "content-stats":
        out = tool.content_stats(interval=a.interval, through=a.through)
    else:
        out = tool.usage_stats(interval=a.interval, through=a.through)
    json.dump(out, sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
