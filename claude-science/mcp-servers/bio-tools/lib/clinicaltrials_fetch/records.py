"""Trimming of a ClinicalTrials.gov v2 study record to the standardized compact form."""

from __future__ import annotations

from typing import Any


def trim_study(study: dict[str, Any]) -> dict[str, Any]:
    """Map one /api/v2/studies record (already field-trimmed server-side) to the
    standardized compact record. Missing modules/values become None or []."""
    ps = study.get("protocolSection", {}) or {}
    ident = ps.get("identificationModule", {}) or {}
    status = ps.get("statusModule", {}) or {}
    sponsor = (ps.get("sponsorCollaboratorsModule", {}) or {}).get("leadSponsor", {}) or {}
    cond = ps.get("conditionsModule", {}) or {}
    design = ps.get("designModule", {}) or {}
    arms = ps.get("armsInterventionsModule", {}) or {}
    locations = (ps.get("contactsLocationsModule", {}) or {}).get("locations", []) or []
    enroll = design.get("enrollmentInfo", {}) or {}
    pcd = status.get("primaryCompletionDateStruct", {}) or {}

    countries = sorted({loc.get("country") for loc in locations if loc.get("country")})
    interventions = [
        {"type": iv.get("type"), "name": iv.get("name")}
        for iv in (arms.get("interventions", []) or [])
    ]

    return {
        "nctId": ident.get("nctId"),
        "briefTitle": ident.get("briefTitle"),
        "overallStatus": status.get("overallStatus"),
        "phases": list(design.get("phases", []) or []),
        "studyType": design.get("studyType"),
        "conditions": list(cond.get("conditions", []) or []),
        "interventions": interventions,
        "enrollmentCount": enroll.get("count"),
        "enrollmentType": enroll.get("type"),
        "primaryCompletionDate": pcd.get("date"),
        "leadSponsorName": sponsor.get("name"),
        "leadSponsorClass": sponsor.get("class"),
        "locationCountries": countries,
    }
