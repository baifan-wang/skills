"""Battery runner: combine attribute groups into the minimal number of requests.

The legacy pybiomart pattern issues one ``Dataset.query()`` per attribute
group. Here, battery items that share an identical filter specification are
merged into a single martservice request that asks for the union of their
attributes; each item's table is then projected back out of the combined
result. Projections that drop columns are de-duplicated (a combined request
containing transcript-level attributes returns one row per transcript, so the
gene-level projection collapses back to one row per gene).
"""

from __future__ import annotations

import json
from typing import Mapping

from .client import BiomartClient, QueryResult


def plan_requests(battery: Mapping) -> list:
    """Group battery items by identical filter specification.

    Returns a list of dicts: ``{"items": [item, ...], "attributes": [...],
    "filters": {...}}`` where ``attributes`` is the order-preserving union of
    the member items' attribute sets.
    """
    attribute_sets = battery["attribute_sets"]
    groups: dict = {}
    order: list = []
    for item in battery["items"]:
        signature = json.dumps(item["filters"], sort_keys=True)
        if signature not in groups:
            groups[signature] = {"items": [], "attributes": [], "filters": item["filters"]}
            order.append(signature)
        group = groups[signature]
        group["items"].append(item)
        for attr in attribute_sets[item["attribute_set"]]:
            if attr not in group["attributes"]:
                group["attributes"].append(attr)
    return [groups[sig] for sig in order]


def run_battery(battery: Mapping, client: BiomartClient | None = None) -> dict:
    """Run the full battery with the minimal number of martservice requests.

    Returns ``{item_id: QueryResult}`` with deterministic (sorted) row order.
    """
    if client is None:
        client = BiomartClient(battery.get("host", "https://www.ensembl.org/biomart/martservice"))
    dataset = battery["dataset"]
    virtual_schema = battery.get("virtual_schema", "default")
    attribute_sets = battery["attribute_sets"]

    results: dict = {}
    for group in plan_requests(battery):
        combined = client.query(
            dataset,
            group["attributes"],
            group["filters"],
            virtual_schema=virtual_schema,
            sort=True,
        )
        for item in group["items"]:
            columns = attribute_sets[item["attribute_set"]]
            deduplicate = set(columns) != set(group["attributes"])
            results[item["id"]] = combined.select(columns, deduplicate=deduplicate, sort=True)
    return results
