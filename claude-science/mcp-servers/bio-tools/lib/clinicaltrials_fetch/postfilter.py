"""Local record-vs-spec consistency checks.

All nine filter dimensions of FilterSpec are expressed server-side, so the tool applies
NO local post-filtering when retrieving a battery spec. This module provides
`record_matches`, which checks a *trimmed* record against the structured dimensions of a
spec. It is used by the accuracy gate as an extra per-record consistency verification,
and would be the post-filter primitive if a future dimension ever needed local filtering.

Notes on what is checked locally:
  - overall_status, study_type, lead_sponsor_class : exact enum equality
  - phase                                          : membership (any requested phase in record phases)
  - location_country                               : membership in locationCountries
  - enrollment                                     : count within inclusive range (skipped if absent)
  - primary_completion_date / first_posted_date    : date checks; partial dates ("2020", "2020-06")
    are expanded to their full possible interval and checked for OVERLAP with the spec range
    (lenient, mirroring how the API treats partial dates). first_posted_date is not present in
    the trimmed record, so it is skipped here.
  - condition / intervention                       : NOT checked locally. The API's Essie engine
    matches these against synonym/term expansions (e.g. "non-small cell lung cancer" matches
    "Carcinoma, Non-Small-Cell Lung"), which a string comparison cannot reproduce.
"""

from __future__ import annotations

import calendar
from typing import Any

from .spec import FilterSpec


def expand_partial_date(value: str) -> tuple[str, str]:
    """Expand a (possibly partial) CTGov date to its inclusive [first, last] day interval.

    "2020"       -> ("2020-01-01", "2020-12-31")
    "2020-06"    -> ("2020-06-01", "2020-06-30")
    "2020-06-15" -> ("2020-06-15", "2020-06-15")
    """
    parts = value.split("-")
    if len(parts) == 1:
        y = int(parts[0])
        return f"{y:04d}-01-01", f"{y:04d}-12-31"
    if len(parts) == 2:
        y, m = int(parts[0]), int(parts[1])
        last = calendar.monthrange(y, m)[1]
        return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last:02d}"
    return value, value


def _date_in_range(value: str | None, start: str | None, end: str | None) -> bool:
    """Lenient check: the possible interval of `value` overlaps [start, end]."""
    if value is None:
        return False
    lo, hi = expand_partial_date(value)
    if start is not None and hi < start:
        return False
    if end is not None and lo > end:
        return False
    return True


def record_matches(record: dict[str, Any], spec: FilterSpec,
                   check_dates: bool = True) -> tuple[bool, list[str]]:
    """Check one trimmed record against the locally-checkable dimensions of `spec`.

    Returns (ok, reasons) where reasons lists every failed dimension."""
    reasons: list[str] = []

    if spec.overall_status and record.get("overallStatus") not in spec.overall_status:
        reasons.append(f"overallStatus={record.get('overallStatus')!r} not in {list(spec.overall_status)}")

    if spec.phase:
        rec_phases = set(record.get("phases") or [])
        if not rec_phases.intersection(spec.phase):
            reasons.append(f"phases={sorted(rec_phases)} disjoint from {list(spec.phase)}")

    if spec.study_type is not None and record.get("studyType") != spec.study_type:
        reasons.append(f"studyType={record.get('studyType')!r} != {spec.study_type!r}")

    if spec.lead_sponsor_class is not None and record.get("leadSponsorClass") != spec.lead_sponsor_class:
        reasons.append(f"leadSponsorClass={record.get('leadSponsorClass')!r} != {spec.lead_sponsor_class!r}")

    if spec.location_country is not None:
        countries = record.get("locationCountries") or []
        if spec.location_country not in countries:
            reasons.append(f"location_country {spec.location_country!r} not in {countries}")

    if spec.enrollment is not None:
        count = record.get("enrollmentCount")
        if count is not None:
            if spec.enrollment.min is not None and count < spec.enrollment.min:
                reasons.append(f"enrollmentCount={count} < min {spec.enrollment.min}")
            if spec.enrollment.max is not None and count > spec.enrollment.max:
                reasons.append(f"enrollmentCount={count} > max {spec.enrollment.max}")

    if check_dates and spec.primary_completion_date is not None:
        if not _date_in_range(record.get("primaryCompletionDate"),
                              spec.primary_completion_date.start,
                              spec.primary_completion_date.end):
            reasons.append(
                f"primaryCompletionDate={record.get('primaryCompletionDate')!r} outside "
                f"[{spec.primary_completion_date.start},{spec.primary_completion_date.end}]")

    return (len(reasons) == 0, reasons)
