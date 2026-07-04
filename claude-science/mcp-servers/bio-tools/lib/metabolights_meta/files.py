"""Study file listings and pattern-based data-file search.

Closes the two PARTIAL coverage items vs tooluniverse/metabolights:
  metabolights_get_study_files      -> get_study_files(accession)
  metabolights_get_study_data_files -> search_data_files(accession, pattern)

Routes (public; no user token needed):
  GET /studies/{id}/files?include_raw_data={bool}
      -> top-level study folder listing (metadata files + folder entries such
         as FILES / AUDIT_FILES / INTERNAL_FILES). Carries volatile
         ``createdAt``/``timestamp`` fields that change between requests —
         they are DROPPED from the records this module emits so output is
         deterministic.
  GET /studies/{id}/public-data-files?search_pattern={glob}&file_match={bool}&folder_match={bool}
      -> recursive listing of the data folder (the FILES tree). The service
         requires at least one of file_match/folder_match to be true and
         answers private/unknown studies with HTTP 401.

The raw-data listing inside the FILES folder is exactly what the top-level
/files route does NOT show; ``get_study_files(include_data_files=True)``
stitches both routes into one record.
"""

from __future__ import annotations

import fnmatch
from typing import Any, Dict, List, Optional

from .client import MetaboLightsClient, MetaboLightsHTTPError
from .meta import _ACCESSION_RE


def _validate_accession(accession: str) -> str:
    accession = accession.strip().upper()
    if not _ACCESSION_RE.match(accession):
        raise ValueError(f"not a MetaboLights accession: {accession!r}")
    return accession


def _slim_file_entry(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Keep stable fields only (createdAt/timestamp are volatile upstream)."""
    return {
        "file": raw.get("file"),
        "type": raw.get("type"),
        "status": raw.get("status"),
        "directory": bool(raw.get("directory")),
    }


def get_study_files(
    accession: str,
    include_raw_data: bool = True,
    include_data_files: bool = True,
    client: Optional[MetaboLightsClient] = None,
) -> Dict[str, Any]:
    """Complete file inventory for a public study.

    ``study_folder`` lists the top-level study directory (ISA-Tab metadata
    files, MAF tables, and folder entries). ``data_files`` recursively lists
    the FILES data folder via the public-data-files route (set
    ``include_data_files=False`` to skip that second request).

    Sorted deterministically; volatile timestamp fields are dropped.
    """
    accession = _validate_accession(accession)
    client = client or MetaboLightsClient()

    payload = client.get_json(
        f"/studies/{accession}/files",
        params={"include_raw_data": str(bool(include_raw_data)).lower()},
    )
    entries = [_slim_file_entry(e) for e in payload.get("study") or []]
    entries.sort(key=lambda e: (not e["directory"], e["file"] or ""))

    record: Dict[str, Any] = {
        "accession": accession,
        "latest_version": payload.get("latest"),
        "study_folder": entries,
        "n_study_folder_entries": len(entries),
        "metadata_files": sorted(
            e["file"] for e in entries
            if (e["type"] or "").startswith("metadata")
        ),
    }

    if include_data_files:
        data = search_data_files(accession, client=client)
        record["data_files"] = data["files"]
        record["n_data_files"] = data["n_files"]

    return record


def search_data_files(
    accession: str,
    pattern: Optional[str] = None,
    file_match: bool = True,
    folder_match: bool = False,
    client: Optional[MetaboLightsClient] = None,
) -> Dict[str, Any]:
    """Pattern-based search over a public study's data folder (FILES tree).

    ``pattern`` is a glob (e.g. ``*.mzML``, ``*.zip``); ``None`` lists every
    data file. At least one of ``file_match``/``folder_match`` must be true
    (upstream constraint — the service 401s otherwise, which this function
    converts to a ValueError before any request is made).

    Results are relative paths under the study folder (``FILES/...``),
    sorted. The service applies the pattern server-side; as a defensive
    cross-check the pattern is re-applied client-side with fnmatch so a
    server-side semantics change surfaces as a hard error rather than a
    silently different listing.
    """
    accession = _validate_accession(accession)
    if not (file_match or folder_match):
        raise ValueError("at least one of file_match/folder_match must be True")
    client = client or MetaboLightsClient()

    params: Dict[str, Any] = {
        "file_match": str(bool(file_match)).lower(),
        "folder_match": str(bool(folder_match)).lower(),
    }
    if pattern is not None:
        params["search_pattern"] = pattern

    payload = client.get_json(f"/studies/{accession}/public-data-files", params=params)
    names: List[str] = sorted(
        e["name"] for e in payload.get("files") or [] if e.get("name")
    )

    if pattern is not None and file_match and not folder_match:
        mismatched = [n for n in names
                      if not fnmatch.fnmatch(n.rsplit("/", 1)[-1], pattern)]
        if mismatched:
            raise MetaboLightsHTTPError(
                f"server returned {len(mismatched)} entries not matching "
                f"pattern {pattern!r} (first: {mismatched[0]!r}); "
                "upstream pattern semantics may have changed"
            )

    return {
        "accession": accession,
        "pattern": pattern,
        "file_match": file_match,
        "folder_match": folder_match,
        "files": names,
        "n_files": len(names),
    }
