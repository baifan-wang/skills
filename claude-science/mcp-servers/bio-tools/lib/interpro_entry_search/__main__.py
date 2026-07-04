"""CLI: python -m interpro_entry_search <command> [args]

Commands
--------
search <query> [--type T] [--db DB] [--go GO:xxxxxxx]
entry <IPR...|PF...>
clans <query>
clan-members <CLxxxx>
proteins <PFxxxxx> [--reviewed] [--tax-id N] [--count-only]
proteomes <PFxxxxx> [--count-only]

Default output is compact JSON (machine mode); --pretty indents.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import (
    clan_members,
    entry_proteins,
    entry_proteomes,
    get_entry,
    search_clans,
    search_entries,
)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="interpro_entry_search")
    p.add_argument("--pretty", action="store_true", help="indented JSON output")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("search", help="InterPro/member-DB entry keyword search")
    sp.add_argument("query")
    sp.add_argument("--type", dest="entry_type", default=None)
    sp.add_argument("--db", dest="source_db", default="interpro")
    sp.add_argument("--go", dest="go_term", default=None)

    ep = sub.add_parser("entry", help="entry detail (IPR or PF accession)")
    ep.add_argument("accession")

    cp = sub.add_parser("clans", help="Pfam clan keyword search")
    cp.add_argument("query")

    cm = sub.add_parser("clan-members", help="member families of a clan")
    cm.add_argument("clan")

    pr = sub.add_parser("proteins", help="member proteins of a Pfam family")
    pr.add_argument("pf_acc")
    pr.add_argument("--reviewed", action="store_true")
    pr.add_argument("--tax-id", dest="tax_id", default=None)
    pr.add_argument("--count-only", action="store_true")

    pm = sub.add_parser("proteomes", help="proteomes containing a Pfam family")
    pm.add_argument("pf_acc")
    pm.add_argument("--count-only", action="store_true")

    a = p.parse_args(argv)

    if a.cmd == "search":
        out = search_entries(a.query, entry_type=a.entry_type, source_db=a.source_db, go_term=a.go_term)
    elif a.cmd == "entry":
        out = get_entry(a.accession)
    elif a.cmd == "clans":
        out = search_clans(a.query)
    elif a.cmd == "clan-members":
        out = clan_members(a.clan)
    elif a.cmd == "proteins":
        out = entry_proteins(a.pf_acc, reviewed_only=a.reviewed, tax_id=a.tax_id, count_only=a.count_only)
    else:
        out = entry_proteomes(a.pf_acc, count_only=a.count_only)

    if a.pretty:
        json.dump(out, sys.stdout, indent=2, sort_keys=True)
    else:
        json.dump(out, sys.stdout, sort_keys=True, separators=(",", ":"))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
