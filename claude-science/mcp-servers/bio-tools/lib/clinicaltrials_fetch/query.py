"""Translation of a FilterSpec into ClinicalTrials.gov v2 API query parameters.

Server-side mapping (all nine supported filter dimensions are expressed server-side;
the tool applies NO local post-filtering for any of them):

  condition                    -> query.cond                 (Essie, ConditionSearch area)
  intervention                 -> query.intr                 (Essie, InterventionSearch area)
  overall_status               -> filter.overallStatus       (pipe-separated enum list)
  phase                        -> filter.advanced AREA[Phase]X        (OR across values)
  study_type                   -> filter.advanced AREA[StudyType]X
  enrollment (int range)       -> filter.advanced AREA[EnrollmentCount]RANGE[min,max]
  primary_completion_date      -> filter.advanced AREA[PrimaryCompletionDate]RANGE[start,end]
  first_posted_date            -> filter.advanced AREA[StudyFirstPostDate]RANGE[start,end]
  location_country             -> filter.advanced AREA[LocationCountry]"X"
  lead_sponsor_class           -> filter.advanced AREA[LeadSponsorClass]X

Open range bounds use the Essie keywords MIN / MAX.
AREA names verified against GET /api/v2/studies/metadata piece names (API 2.0.5).
"""

from __future__ import annotations

from .spec import FilterSpec


def _quote(value: str) -> str:
    """Quote a free-text Essie operand (escape embedded double quotes)."""
    return '"' + value.replace('"', '\\"') + '"'


def _date_range_expr(area: str, start: str | None, end: str | None) -> str:
    lo = start if start is not None else "MIN"
    hi = end if end is not None else "MAX"
    return f"AREA[{area}]RANGE[{lo},{hi}]"


def _int_range_expr(area: str, lo_v: int | None, hi_v: int | None) -> str:
    lo = str(lo_v) if lo_v is not None else "MIN"
    hi = str(hi_v) if hi_v is not None else "MAX"
    return f"AREA[{area}]RANGE[{lo},{hi}]"


def build_advanced_expr(spec: FilterSpec) -> str | None:
    """Build the filter.advanced Essie expression (deterministic term order)."""
    terms: list[str] = []
    if spec.phase:
        if len(spec.phase) == 1:
            terms.append(f"AREA[Phase]{spec.phase[0]}")
        else:
            terms.append("(" + " OR ".join(f"AREA[Phase]{p}" for p in spec.phase) + ")")
    if spec.study_type is not None:
        terms.append(f"AREA[StudyType]{spec.study_type}")
    if spec.enrollment is not None:
        terms.append(_int_range_expr("EnrollmentCount", spec.enrollment.min, spec.enrollment.max))
    if spec.primary_completion_date is not None:
        terms.append(_date_range_expr("PrimaryCompletionDate",
                                      spec.primary_completion_date.start,
                                      spec.primary_completion_date.end))
    if spec.first_posted_date is not None:
        terms.append(_date_range_expr("StudyFirstPostDate",
                                      spec.first_posted_date.start,
                                      spec.first_posted_date.end))
    if spec.location_country is not None:
        terms.append(f"AREA[LocationCountry]{_quote(spec.location_country)}")
    if spec.lead_sponsor_class is not None:
        terms.append(f"AREA[LeadSponsorClass]{spec.lead_sponsor_class}")
    return " AND ".join(terms) if terms else None


def build_query_params(spec: FilterSpec) -> dict[str, str]:
    """Base query parameters for /api/v2/studies (without paging/fields keys)."""
    params: dict[str, str] = {}
    if spec.condition is not None:
        params["query.cond"] = spec.condition
    if spec.intervention is not None:
        params["query.intr"] = spec.intervention
    if spec.overall_status:
        params["filter.overallStatus"] = "|".join(spec.overall_status)
    adv = build_advanced_expr(spec)
    if adv is not None:
        params["filter.advanced"] = adv
    return params


def build_count_params(spec: FilterSpec) -> dict[str, str]:
    """Parameters for an independent count-only request (ground truth for the gate)."""
    params = build_query_params(spec)
    params.update({"countTotal": "true", "pageSize": "1", "fields": "NCTId"})
    return params


def build_crosscheck_params(spec: FilterSpec) -> dict[str, str]:
    """Reformulated query for the gate cross-check.

    The condition is moved from query.cond into an explicit
    query.term=AREA[ConditionSearch](...) Essie expression (and likewise the
    intervention into AREA[InterventionSearch](...)); all other filters are
    unchanged. A correct translation must return the identical NCT ID set.
    """
    params: dict[str, str] = {}
    term_parts: list[str] = []
    if spec.condition is not None:
        term_parts.append(f"AREA[ConditionSearch]({spec.condition})")
    if spec.intervention is not None:
        term_parts.append(f"AREA[InterventionSearch]({spec.intervention})")
    if term_parts:
        params["query.term"] = " AND ".join(term_parts)
    if spec.overall_status:
        params["filter.overallStatus"] = "|".join(spec.overall_status)
    adv = build_advanced_expr(spec)
    if adv is not None:
        params["filter.advanced"] = adv
    return params


def build_naive_term(spec: FilterSpec) -> str:
    """The 'legacy baseline' query string for the benchmark comparison.

    This reproduces what an agent typically does today: cram all filter terms into a
    single query.term full-text search, lower-cased, with enum underscores replaced by
    spaces, and date/numeric ranges omitted (they cannot be expressed as plain text).
    Issued as ONE GET with default pageSize (10) and default fields, no pagination.
    """
    words: list[str] = []
    if spec.condition:
        words.append(spec.condition)
    if spec.intervention:
        words.append(spec.intervention)
    for s in spec.overall_status:
        words.append(s.replace("_", " ").lower())
    for p in spec.phase:
        words.append(p.replace("_", " ").lower())
    if spec.study_type:
        words.append(spec.study_type.replace("_", " ").lower())
    if spec.location_country:
        words.append(spec.location_country)
    if spec.lead_sponsor_class:
        words.append(spec.lead_sponsor_class.replace("_", " ").lower())
    return " ".join(words)
