"""Parsing of GEO SOFT *brief* text (header lines only, no data tables).

geo_meta only ever requests ``view=brief`` SOFT text from
``https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi`` with ``targ=self`` (the series
header block) and ``targ=gsm`` (sample header blocks). Brief view contains no
data tables, and platform records are never requested (their listings can be
multi-MB even in brief view).
"""

from __future__ import annotations

import re
from typing import Iterable

_ENTITY_RE = re.compile(r"^\^(?P<kind>[A-Z]+) = (?P<acc>\S+)\s*$")
_ATTR_RE = re.compile(r"^!(?P<key>[^=]+?)\s*=\s*(?P<value>.*?)\s*$")


def split_entities(soft_text: str) -> list[tuple[str, str, dict[str, list[str]]]]:
    """Split brief SOFT text into (kind, accession, attributes) tuples.

    Attributes map ``!Key`` (without the leading ``!``) to the *list* of values in
    file order, because keys such as ``Sample_characteristics_ch1`` and
    ``Series_supplementary_file`` legitimately repeat.
    """
    entities: list[tuple[str, str, dict[str, list[str]]]] = []
    current: dict[str, list[str]] | None = None
    for raw_line in soft_text.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line:
            continue
        m = _ENTITY_RE.match(line)
        if m:
            current = {}
            entities.append((m.group("kind"), m.group("acc"), current))
            continue
        if current is None:
            continue
        a = _ATTR_RE.match(line)
        if a:
            current.setdefault(a.group("key"), []).append(a.group("value"))
    return entities


def _first(attrs: dict[str, list[str]], key: str) -> str | None:
    vals = attrs.get(key)
    return vals[0] if vals else None


def _all(attrs: dict[str, list[str]], key: str) -> list[str]:
    return list(attrs.get(key, []))


def parse_characteristics(values: Iterable[str]) -> list[dict[str, str]]:
    """Parse ``!Sample_characteristics_ch1`` values into {tag, value} pairs.

    GEO convention is ``tag: value``; lines without a colon are kept verbatim with
    an empty tag so no information is dropped.
    """
    out: list[dict[str, str]] = []
    for v in values:
        if ": " in v:
            tag, val = v.split(": ", 1)
            out.append({"tag": tag.strip(), "value": val.strip()})
        elif v.endswith(":") and v.count(":") == 1:
            out.append({"tag": v[:-1].strip(), "value": ""})
        else:
            out.append({"tag": "", "value": v.strip()})
    return out


def parse_series_header(soft_text: str) -> dict:
    """Parse a ``targ=self`` brief SOFT response into a series-header dict."""
    entities = split_entities(soft_text)
    series = [(acc, attrs) for kind, acc, attrs in entities if kind == "SERIES"]
    if not series:
        raise ValueError("no ^SERIES block found in SOFT text")
    acc, attrs = series[0]
    return {
        "accession": _first(attrs, "Series_geo_accession") or acc,
        "title": _first(attrs, "Series_title"),
        "status": _first(attrs, "Series_status"),
        "submission_date": _first(attrs, "Series_submission_date"),
        "last_update_date": _first(attrs, "Series_last_update_date"),
        "summary": " ".join(_all(attrs, "Series_summary")),
        "overall_design": " ".join(_all(attrs, "Series_overall_design")),
        "type": _all(attrs, "Series_type"),
        "pubmed_ids": _all(attrs, "Series_pubmed_id"),
        "contributors": _all(attrs, "Series_contributor"),
        "platform_ids": sorted(_all(attrs, "Series_platform_id")),
        "sample_ids": sorted(_all(attrs, "Series_sample_id")),
        "supplementary_files": sorted(_all(attrs, "Series_supplementary_file")),
        "relations": _all(attrs, "Series_relation"),
    }


def parse_sample_headers(soft_text: str) -> list[dict]:
    """Parse a ``targ=gsm`` brief SOFT response into a list of sample dicts.

    Output is sorted by sample accession for deterministic ordering.
    """
    entities = split_entities(soft_text)
    samples: list[dict] = []
    for kind, acc, attrs in entities:
        if kind != "SAMPLE":
            continue
        organisms = _all(attrs, "Sample_organism_ch1") + _all(attrs, "Sample_organism_ch2")
        characteristics = parse_characteristics(
            _all(attrs, "Sample_characteristics_ch1") + _all(attrs, "Sample_characteristics_ch2")
        )
        samples.append(
            {
                "accession": _first(attrs, "Sample_geo_accession") or acc,
                "title": _first(attrs, "Sample_title"),
                "type": _first(attrs, "Sample_type"),
                "source_name": _first(attrs, "Sample_source_name_ch1"),
                "organism": sorted(set(organisms)),
                "taxid": sorted(set(_all(attrs, "Sample_taxid_ch1") + _all(attrs, "Sample_taxid_ch2"))),
                "characteristics": characteristics,
                "molecule": _first(attrs, "Sample_molecule_ch1"),
                "library_strategy": _first(attrs, "Sample_library_strategy"),
                "library_source": _first(attrs, "Sample_library_source"),
                "library_selection": _first(attrs, "Sample_library_selection"),
                "instrument_model": _first(attrs, "Sample_instrument_model"),
                "platform_id": _first(attrs, "Sample_platform_id"),
                "supplementary_files": sorted(
                    v
                    for k, vals in attrs.items()
                    if k.startswith("Sample_supplementary_file")
                    for v in vals
                    if v and v.upper() != "NONE"
                ),
            }
        )
    samples.sort(key=lambda s: s["accession"])
    return samples
