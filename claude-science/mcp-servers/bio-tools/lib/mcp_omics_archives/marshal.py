"""Pure reshaping helpers for mcp-omics-archives (offline-testable).

The MetaboLights fleet tool's flat record deliberately omits protocols and
per-sample rows; the old connector exposed them. Per the build conventions we
reuse the fleet *client* (paced/retrying) to fetch the same raw ISA payload
and reshape the extra blocks here instead of writing new HTTP code.
"""

from __future__ import annotations

from typing import Any


def metabolights_protocols(content: dict[str, Any]) -> list[dict[str, Any]]:
    """``content.protocols`` -> [{"name", "description"}, ...] (input order)."""
    out = []
    for p in content.get("protocols") or []:
        if not isinstance(p, dict):
            continue
        name = (p.get("name") or "").strip() or None
        desc = (p.get("description") or "").strip() or None
        if name or desc:
            out.append({"name": name, "description": desc})
    return out


def metabolights_sample_table(
    sample_table: dict[str, Any] | None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Reshape the raw ISA ``sampleTable`` block into header-keyed row dicts.

    ``fields`` is a dict keyed '<index>~<name>' with {"index", "header", ...};
    ``data`` is a list of positional rows. Rows shorter than the header list are
    padded with ""; ``max_rows`` truncates the output with an explicit flag.
    """
    sample_table = sample_table or {}
    fields = sample_table.get("fields") or {}
    ordered = sorted(
        (f for f in fields.values() if isinstance(f, dict) and "index" in f),
        key=lambda f: f["index"],
    )
    headers = [str(f.get("header") or f"column_{f['index']}") for f in ordered]
    data = sample_table.get("data") or []
    n_total = len(data)
    truncated = max_rows is not None and max_rows >= 0 and n_total > max_rows
    rows = []
    for raw in (data[:max_rows] if truncated else data):
        raw = list(raw) + [""] * (len(headers) - len(raw))
        rows.append(dict(zip(headers, raw)))
    return {
        "headers": headers,
        "rows": rows,
        "n_rows_total": n_total,
        "rows_truncated": truncated,
    }
