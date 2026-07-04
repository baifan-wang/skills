"""Direct Ensembl BioMart martservice client.

Key differences from the legacy pybiomart pattern:

* No configuration round-trip: the query XML is built locally from the
  attribute / filter names the caller already knows, so no request is spent
  fetching the dataset configuration.
* ``completionStamp="1"`` is always requested and the trailing ``[success]``
  marker is verified, so silently truncated responses are detected and
  retried instead of being returned as (shorter) valid-looking TSV.
* Transient failures (connection errors, 5xx, truncated responses) are
  retried with exponential backoff; permanent query rejections
  (``Query ERROR`` / BioMart usage exceptions) raise immediately.
* Rows are returned in a deterministic order (lexicographic sort over the
  row tuple; the first requested attribute is the gene ID in all batteries
  shipped with this tool, so this is "sorted by gene ID").
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import requests

DEFAULT_MARTSERVICE = "https://www.ensembl.org/biomart/martservice"
DEFAULT_VIRTUAL_SCHEMA = "default"
COMPLETION_STAMP = "[success]"


class BiomartError(RuntimeError):
    """Base error for martservice problems."""


class BiomartQueryError(BiomartError):
    """The server rejected the query (bad attribute/filter combination).

    This is a permanent error and is never retried; callers that hit it for an
    attribute combination should split the query into smaller attribute sets.
    """


class BiomartIncompleteResponse(BiomartError):
    """Response arrived without the ``[success]`` completion stamp (truncated)."""


def build_query_xml(
    dataset: str,
    attributes: Sequence[str],
    filters: Mapping[str, object] | None = None,
    *,
    virtual_schema: str = DEFAULT_VIRTUAL_SCHEMA,
    header: bool = False,
    unique_rows: bool = False,
    completion_stamp: bool = True,
) -> str:
    """Build a martservice ``<Query>`` XML document.

    Filter values may be a string, an int, a bool (mapped to BioMart's
    ``only``/``excluded``), or a list/tuple of strings (joined with commas).
    """
    query = ET.Element(
        "Query",
        attrib={
            "virtualSchemaName": virtual_schema,
            "formatter": "TSV",
            "header": "1" if header else "0",
            "uniqueRows": "1" if unique_rows else "0",
            "datasetConfigVersion": "0.6",
            "completionStamp": "1" if completion_stamp else "0",
        },
    )
    ds = ET.SubElement(query, "Dataset", attrib={"name": dataset, "interface": "default"})
    for fname, fvalue in (filters or {}).items():
        if isinstance(fvalue, bool):
            value = "only" if fvalue else "excluded"
        elif isinstance(fvalue, (list, tuple)):
            value = ",".join(str(v) for v in fvalue)
        else:
            value = str(fvalue)
        ET.SubElement(ds, "Filter", attrib={"name": fname, "value": value})
    for attr in attributes:
        ET.SubElement(ds, "Attribute", attrib={"name": attr})
    return (
        '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE Query>'
        + ET.tostring(query, encoding="unicode")
    )


@dataclass
class QueryResult:
    """A parsed TSV result: ``columns`` are the attribute internal names in
    request order; ``rows`` are lists of strings (one per column)."""

    columns: list
    rows: list = field(default_factory=list)

    def to_tsv(self) -> str:
        lines = ["\t".join(self.columns)]
        lines.extend("\t".join(row) for row in self.rows)
        return "\n".join(lines) + "\n"

    def select(self, columns: Sequence[str], *, deduplicate: bool = False, sort: bool = True) -> "QueryResult":
        """Project onto a subset of columns (in the given order), optionally
        de-duplicating rows (used when a combined transcript-level request is
        projected back down to gene-level attributes)."""
        idx = [self.columns.index(c) for c in columns]
        rows = [[row[i] for i in idx] for row in self.rows]
        if deduplicate:
            seen = set()
            unique_rows = []
            for row in rows:
                key = tuple(row)
                if key not in seen:
                    seen.add(key)
                    unique_rows.append(row)
            rows = unique_rows
        if sort:
            rows = sorted(rows)
        return QueryResult(list(columns), rows)

    def __len__(self) -> int:
        return len(self.rows)


class BiomartClient:
    """Thin, instrumented client for the Ensembl BioMart martservice.

    Counts every outbound HTTP request attempt (``request_count``) and the
    payload bytes received (``bytes_downloaded``) so benchmark scripts can
    read them directly.
    """

    def __init__(
        self,
        martservice_url: str = DEFAULT_MARTSERVICE,
        *,
        # Worst-case schedule is timeout×(max_retries+1) + backoffs, and a
        # client-abandoned call grinds it to completion on an aggregate
        # worker thread — keep it minutes, not tens of minutes (the old
        # 300s×5 schedule could pin a thread ~25min; #2875 review).
        timeout: float = 120.0,
        max_retries: int = 2,
        backoff_base: float = 2.0,
        min_request_interval: float = 0.4,
        # BioMart accepts whole-dataset queries; an unbounded read of one
        # builds the entire decoded TSV in the single warm aggregate process
        # (#2875 review, OOM blast radius). 50MB ≈ millions of TSV rows —
        # far past any per-tool battery here; raise deliberately if a future
        # tool truly needs more.
        max_response_bytes: int = 50 * 1024 * 1024,
        session: requests.Session | None = None,
    ) -> None:
        self.martservice_url = martservice_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.min_request_interval = min_request_interval
        self.max_response_bytes = max_response_bytes
        self._session = session or requests.Session()
        self.request_count = 0
        self.bytes_downloaded = 0
        self._last_request_at = 0.0

    # -- public API ---------------------------------------------------------

    def query(
        self,
        dataset: str,
        attributes: Sequence[str],
        filters: Mapping[str, object] | None = None,
        *,
        virtual_schema: str = DEFAULT_VIRTUAL_SCHEMA,
        sort: bool = True,
    ) -> QueryResult:
        """Run a single martservice query and return the parsed TSV.

        Columns are the attribute internal names in request order (the server
        is asked for ``header=0``; column identity is therefore exact and not
        dependent on display-name strings). Rows are sorted lexicographically
        by the full row tuple when ``sort=True`` (deterministic; first column
        is the gene ID for the batteries shipped here).
        """
        attributes = list(attributes)
        xml = build_query_xml(dataset, attributes, filters, virtual_schema=virtual_schema)
        body = self._post(xml)
        rows = self._parse_tsv(body, n_cols=len(attributes))
        if sort:
            rows.sort()
        return QueryResult(attributes, rows)

    # -- internals ----------------------------------------------------------

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)

    def _post(self, xml: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            if attempt:
                time.sleep(self.backoff_base * (2 ** (attempt - 1)))
            self._throttle()
            self.request_count += 1
            self._last_request_at = time.monotonic()
            try:
                resp = self._session.post(
                    self.martservice_url,
                    data={"query": xml},
                    timeout=self.timeout,
                    headers={"Accept-Encoding": "gzip"},
                    stream=True,
                )
                # Bounded read (#2875 review): iter_content yields DECODED
                # bytes, so the cap bounds what actually lands in memory —
                # a whole-dataset query fails loudly instead of building a
                # multi-hundred-MB string in the one warm process.
                chunks: list[bytes] = []
                total = 0
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    total += len(chunk)
                    if total > self.max_response_bytes:
                        resp.close()
                        raise BiomartError(
                            f"martservice response exceeded "
                            f"{self.max_response_bytes} bytes — narrow the "
                            "query (tighter filters / fewer attributes)")
                    chunks.append(chunk)
            except requests.RequestException as exc:
                last_error = exc
                continue
            raw = b"".join(chunks)
            self.bytes_downloaded += len(raw)
            text = raw.decode(resp.encoding or "utf-8", errors="replace")
            if resp.status_code >= 500 or resp.status_code in (405, 429):
                # 405/HTML pages are what Ensembl's status page serves during
                # transient outages; treat as retryable.
                last_error = BiomartError(f"HTTP {resp.status_code} from martservice")
                continue
            if resp.status_code != 200:
                raise BiomartError(f"HTTP {resp.status_code} from martservice: {text[:500]}")
            head = text[:2000]
            if head.lstrip().lower().startswith(("<html", "<!doctype html")):
                last_error = BiomartError(
                    "martservice returned an HTML page (Ensembl outage/maintenance notice)"
                )
                continue
            if (
                text.lstrip().startswith("Query ERROR")
                or "BioMart::Exception" in head
                or head.lstrip().startswith("Problem retrieving")
            ):
                raise BiomartQueryError(text[:1000].strip())
            stripped = text.rstrip("\r\n ")
            if not stripped.endswith(COMPLETION_STAMP):
                last_error = BiomartIncompleteResponse(
                    "response missing the [success] completion stamp (truncated download)"
                )
                continue
            return stripped[: -len(COMPLETION_STAMP)].rstrip("\r\n")
        raise BiomartError(
            f"martservice request failed after {self.max_retries + 1} attempts: {last_error!r}"
        )

    @staticmethod
    def _parse_tsv(body: str, n_cols: int) -> list:
        rows = []
        if not body:
            return rows
        for line in body.replace("\r\n", "\n").split("\n"):
            if line == "":
                continue
            fields = line.split("\t")
            if len(fields) != n_cols:
                raise BiomartError(
                    f"malformed TSV line: expected {n_cols} columns, got {len(fields)}: {line[:200]!r}"
                )
            rows.append(fields)
        return rows
