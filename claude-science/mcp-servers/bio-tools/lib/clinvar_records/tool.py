"""High-level ClinVar retrieval: search, batch records, rsID lookup.

Honesty rules: every listing carries the API's own total (``total``) and a
``truncated`` flag when the returned page is a capped prefix; batch lookups
report ``not_found`` explicitly and ``not_processed`` when a wall-clock
deadline cuts the batch short (MCP transport budget).
"""
from __future__ import annotations

import re
import time

from .client import ClinVarClient
from .records import parse_summary_doc

# esummary accepts hundreds of ids per POST; keep one request per tool call.
MAX_SEARCH_RETMAX = 200
MAX_BATCH_ACCESSIONS = 50
_VCV_RE = re.compile(r"^VCV(\d+)(?:\.\d+)?$", re.IGNORECASE)
_RCV_RE = re.compile(r"^RCV\d+(?:\.\d+)?$", re.IGNORECASE)
_RSID_RE = re.compile(r"^rs\d+$", re.IGNORECASE)


class ClinVarRecords:
    """ClinVar esearch/esummary orchestration over a paced client."""

    def __init__(self, client: ClinVarClient) -> None:
        self.client = client

    # -- search --------------------------------------------------------------

    def search(self, term: str, retmax: int) -> dict:
        """esearch + esummary: term -> {total, truncated, records}."""
        retmax = max(1, min(int(retmax), MAX_SEARCH_RETMAX))
        result = self.client.esearch(term, retmax=retmax)
        total = int(result.get("count", 0))
        uids = list(result.get("idlist") or [])
        missing: list[str] = []
        records = self._summaries(uids, missing=missing)
        return {
            "term": term,
            "total": total,
            "n_returned": len(records),
            # capped page vs. upstream dropping a summary doc are different
            # conditions: truncation is judged against the UID page esearch
            # returned; dropped docs are reported in missing_uids.
            "truncated": total > len(uids),
            "missing_uids": missing,
            "records": records,
        }

    # -- batch by accession ----------------------------------------------------

    def records_by_accessions(self, accessions: list[str],
                              deadline_s: float = 40.0) -> dict:
        """Fetch full records for VCV/RCV accessions (or bare variation IDs).

        VCV accessions and numeric variation IDs resolve locally (the UID is
        the VCV number); each RCV accession costs one esearch. ``deadline_s``
        bounds RCV resolution wall-clock — unresolved inputs are returned in
        ``not_processed`` rather than blowing the transport budget.
        """
        cleaned = [a.strip() for a in accessions if a and a.strip()]
        # Cap on the UNIQUE set (finding 3406986022): the esummary/esearch
        # fan-out is keyed to unique accessions, so a batch whose raw count
        # exceeds the cap but whose unique count is within it (duplicate /
        # overlapping VCV lists) must not be spuriously rejected — matches
        # the fleet siblings (dbsnp get_rsids, alphafold fetch_coverage).
        pending = list(dict.fromkeys(cleaned))  # dedupe, keep order
        n_duplicate_skipped = len(cleaned) - len(pending)
        if len(pending) > MAX_BATCH_ACCESSIONS:
            raise ValueError(
                f"too many accessions ({len(pending)} unique); max "
                f"{MAX_BATCH_ACCESSIONS} per call")
        uid_sources: dict[str, list[str]] = {}  # uid -> input accessions
        not_found: list[str] = []
        not_processed: list[str] = []
        # Pass 1 — local-only resolution (VCV/numeric: the UID is the VCV
        # number) + input validation; no network, so never deadline-bound.
        rcvs: list[str] = []
        for acc in pending:
            m = _VCV_RE.match(acc)
            if m:
                uid_sources.setdefault(str(int(m.group(1))), []).append(acc)
                continue
            if acc.isdigit():
                uid_sources.setdefault(str(int(acc)), []).append(acc)
                continue
            if _RCV_RE.match(acc):
                rcvs.append(acc)
                continue
            if _RSID_RE.match(acc):
                raise ValueError(
                    f"{acc!r} is an rsID — use the rsID lookup instead")
            raise ValueError(
                f"unrecognized accession {acc!r} (expected VCVnnn, RCVnnn, "
                "or a bare ClinVar variation ID)")
        # Pass 2 — RCVs (one esearch each); only these can trip the
        # wall-clock deadline, so only RCVs land in not_processed.
        t0 = time.monotonic()
        for i, acc in enumerate(rcvs):
            if time.monotonic() - t0 > deadline_s:
                not_processed.extend(rcvs[i:])
                break
            result = self.client.esearch(acc.upper().split(".")[0],
                                         retmax=5)
            uids = list(result.get("idlist") or [])
            if not uids:
                not_found.append(acc)
            for uid in uids:
                uid_sources.setdefault(uid, []).append(acc)
        missing_uids: list[str] = []
        records = self._summaries([u for u in uid_sources
                                   if u not in ("", None)],
                                  missing=missing_uids, sources=uid_sources)
        # order is undefined for a batch lookup: sort for determinism
        records.sort(key=lambda r: r["variation_id"])
        return {
            "n_requested": len(cleaned),
            "n_unique": len(pending),
            "n_duplicate_skipped": n_duplicate_skipped,
            "records": records,
            "not_found": sorted(set(not_found)),
            "missing_uids": sorted(set(missing_uids)),
            "not_processed": not_processed,
        }

    # -- rsID ------------------------------------------------------------------

    def records_by_rsid(self, rsid: str, retmax: int) -> dict:
        """rsID -> all ClinVar variation records mentioning it."""
        rsid = rsid.strip()
        if not _RSID_RE.match(rsid):
            raise ValueError(f"not an rsID: {rsid!r} (expected e.g. rs7412)")
        retmax = max(1, min(int(retmax), MAX_SEARCH_RETMAX))
        result = self.client.esearch(rsid.lower(), retmax=retmax)
        total = int(result.get("count", 0))
        uids = list(result.get("idlist") or [])
        missing: list[str] = []
        records = self._summaries(uids, missing=missing)
        return {
            "rsid": rsid.lower(),
            "total": total,
            "n_returned": len(records),
            "truncated": total > len(uids),
            "missing_uids": missing,
            "records": records,
        }

    # -- internals ----------------------------------------------------------------

    def _summaries(self, uids: list[str], missing: list[str] | None = None,
                   sources: dict[str, list[str]] | None = None) -> list[dict]:
        """Batch esummary -> parsed records (one POST), in input UID order
        (esearch order is ClinVar's relevance/recency ranking — callers
        that need a different order sort the result). UIDs whose esummary
        doc is absent or errored are appended to ``missing`` (by source
        accession when known)."""
        if not uids:
            return []
        result = self.client.esummary(uids)
        records = []
        for uid in uids:
            doc = result.get(str(uid))
            if not isinstance(doc, dict) or doc.get("error"):
                if missing is not None:
                    missing.extend((sources or {}).get(uid, [uid]))
                continue
            rec = parse_summary_doc(doc)
            if sources is not None:
                rec["requested_as"] = sources.get(uid, [])
            records.append(rec)
        return records
