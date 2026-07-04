"""Run declarative specs against the openFDA label endpoint."""

from __future__ import annotations

import json

from .client import OpenFDAClient
from .extract import extract_record, extract_sections
from .spec import build_search


def _sort_key(record: dict) -> tuple:
    return (record.get("set_id") or "", record.get("spl_id") or record.get("id") or "")


def run_spec(
    spec: dict,
    client: OpenFDAClient,
    sections: list[str] | None = None,
    keep_raw: bool = False,
) -> dict:
    """Complete retrieval for one declarative spec.

    Returns::

        {
          "spec_id":   spec.get("id"),
          "search":    the generated search string,
          "total":     meta.results.total reported by the API,
          "count":     number of records actually retrieved,
          "records":   [structured records, sorted by (set_id, spl_id)],
          "raw":       [raw label documents, same order]   # only if keep_raw
        }

    If ``sections`` is given, records come from ``extract_sections`` (targeted,
    token-lean) instead of the default ``extract_record``.
    """
    search = build_search(spec)
    raw_records, total = client.fetch_all(search)
    raw_records = sorted(raw_records, key=lambda r: (r.get("set_id") or "", r.get("id") or ""))
    if sections:
        records = [extract_sections(r, sections) for r in raw_records]
    else:
        records = [extract_record(r) for r in raw_records]
    records = sorted(records, key=_sort_key)
    out = {
        "spec_id": spec.get("id"),
        "search": search,
        "total": total,
        "count": len(records),
        "records": records,
    }
    if keep_raw:
        out["raw"] = raw_records
    return out


def run_battery(
    battery_path: str,
    client: OpenFDAClient,
    sections: list[str] | None = None,
    keep_raw: bool = False,
) -> list[dict]:
    """Run every spec in a battery.json file, in file order."""
    with open(battery_path) as fh:
        battery = json.load(fh)
    return [run_spec(spec, client, sections=sections, keep_raw=keep_raw)
            for spec in battery["specs"]]


def to_jsonl(spec_results: list[dict]) -> str:
    """Serialize battery results as JSON Lines (one structured record per line),
    with stable key order — this is the tool's primary output representation."""
    lines = []
    for res in spec_results:
        for rec in res["records"]:
            lines.append(json.dumps({"spec_id": res["spec_id"], **rec}, sort_keys=True))
    return "\n".join(lines) + ("\n" if lines else "")
