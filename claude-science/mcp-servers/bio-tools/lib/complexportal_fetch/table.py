"""Compact tabular / JSON renderings of structured records (token-lean output)."""
from __future__ import annotations

import json

PARTICIPANT_COLUMNS = [
    "complex_ac", "complex_name", "species_name", "taxid", "evidence_eco",
    "participant_identifier", "participant_name", "interactor_type",
    "biological_role", "stoichiometry_min", "stoichiometry_max",
]

COMPLEX_COLUMNS = [
    "complex_ac", "name", "systematic_name", "species_name", "taxid",
    "predicted_complex", "evidence_eco", "n_participants",
    "go_ids", "xref_databases",
]

SEARCH_COLUMNS = [
    "query_accession", "complex_ac", "complex_name", "species_name", "taxid",
    "predicted_complex", "n_interactors",
]


def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v).replace("\t", " ").replace("\n", " ").replace("\r", " ")


def records_to_tsv(records: list[dict], level: str = "participant") -> str:
    """Render structured complex records as a TSV table.

    level='participant': one row per (complex, participant).
    level='complex':     one row per complex (GO ids and xref databases summarized).
    """
    rows: list[list[str]] = []
    if level == "participant":
        header = PARTICIPANT_COLUMNS
        for r in records:
            for p in r["participants"]:
                rows.append([
                    _cell(r["complex_ac"]), _cell(r["name"]), _cell(r["species_name"]),
                    _cell(r["taxid"]), _cell(r["evidence"]["eco_code"]),
                    _cell(p["identifier"]), _cell(p["name"]), _cell(p["interactor_type"]),
                    _cell(p["biological_role"]), _cell(p["stoichiometry_min"]),
                    _cell(p["stoichiometry_max"]),
                ])
    elif level == "complex":
        header = COMPLEX_COLUMNS
        for r in records:
            rows.append([
                _cell(r["complex_ac"]), _cell(r["name"]), _cell(r["systematic_name"]),
                _cell(r["species_name"]), _cell(r["taxid"]), _cell(r["predicted_complex"]),
                _cell(r["evidence"]["eco_code"]), _cell(len(r["participants"])),
                _cell(",".join(g["go_id"] for g in r["go_annotations"])),
                _cell(",".join(sorted({x["database"] for x in r["cross_references"]}))),
            ])
    else:
        raise ValueError(f"unknown level: {level!r}")
    lines = ["\t".join(header)] + ["\t".join(row) for row in rows]
    return "\n".join(lines) + "\n"


def search_to_tsv(search_results: list[dict]) -> str:
    """Render search_by_participant() results as a TSV table (one row per hit)."""
    lines = ["\t".join(SEARCH_COLUMNS)]
    for s in search_results:
        for c in s["complexes"]:
            lines.append("\t".join([
                _cell(s["query_accession"]), _cell(c["complex_ac"]), _cell(c["name"]),
                _cell(c["species_name"]), _cell(c["taxid"]), _cell(c["predicted_complex"]),
                _cell(len(c["interactors"])),
            ]))
    return "\n".join(lines) + "\n"


def records_to_json(obj, indent: int | None = None) -> str:
    """Deterministic JSON serialization (sorted keys, stable separators)."""
    return json.dumps(obj, indent=indent, sort_keys=True, ensure_ascii=False)
