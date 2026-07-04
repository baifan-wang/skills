"""CartBlanche22 (ZINC22) API client — the submit-poll transport.

CRITICAL CONTRACT: every CartBlanche22 search endpoint is ASYNC and
POST-only. A search is a form-encoded POST that returns a task receipt
``{"task": "<uuid>"}``; the result is fetched by polling
``GET /search/result/<uuid>`` until ``status`` is ``SUCCESS`` (or ``result``
is populated). A naive ``GET ?param=value`` returns HTTP 400 or the HTML
SPA shell — the documented drift trap this server exists to remove (the
zinc-database skill ablation showed callers improvising exactly that).
This client encapsulates the whole dance; tools present ONE synchronous
call and never expose the task id except in timeout errors (so a caller
could re-poll by hand).

Rate courtesy: ZINC publishes no hard limit; requests (submits AND polls)
are paced through the process-wide HostPacer at >= 1 s per request, and the
poll loop ticks at POLL_INTERVAL_S — never a tight loop.

Failure taxonomy (every arm raises ZincApiError with an actionable message,
never a stack trace): HTTP 400 (bad parameters), SPA-shell/non-JSON bodies
(request not understood as an API call), missing task receipt, server-side
FAILURE status, transient transport errors (bounded retries on submit), and
poll deadline exhaustion (ZincTaskTimeout names the task uuid).
"""

from __future__ import annotations

import json
import time
from urllib.parse import quote

import requests

from mcp_servers_common.ratelimit import pace, retry_after_seconds

BASE_URL = "https://cartblanche22.docking.org"
FILES_BASE_URL = "https://files.docking.org/zinc22"

# One standard projection for every search: identity + structure +
# purchasability + tranche-encoded properties.
DEFAULT_OUTPUT_FIELDS = "zinc_id,smiles,tranche_name,catalogs"

MIN_INTERVAL_S = 1.0        # politeness floor per request (submit + poll)
POLL_INTERVAL_S = 1.5       # pause between result polls
# Overall submit→result budget. The MCP transport hangs at ~60s, so a
# default at the ceiling defeats the actionable ZincTaskTimeout (which
# names the task uuid for manual re-poll) on the slow-similarity path it
# exists for — the same lesson pubmed's ecitmatch budget encodes (review
# 3415624590). 25s + bounded submit retries + pacing stays well under it.
DEFAULT_TIMEOUT_S = 25.0
MIN_TIMEOUT_S = 5.0
MAX_TIMEOUT_S = 55.0        # hard cap at the transport ceiling - margin
HTTP_TIMEOUT_S = 30.0       # per-request transport timeout CEILING (each
                            # request is further clamped to remaining budget)
SUBMIT_RETRIES = 2          # extra attempts on transient submit failures
# Bounded poll-body read (review 3415652687): a broad similarity query can
# match a large slice of 230M compounds; without a cap the warm shared
# bio-tools process would buffer the whole JSON before max_results applies.
# Same class + same number as biomart_query's max_response_bytes cap.
MAX_RESPONSE_BYTES = 50 * 1024 * 1024

# Result sources, presentation order (current release first).
SOURCE_ORDER = ("zinc22", "zinc20")

_PENDING_STATUSES = frozenset({"PENDING", "STARTED", "PROGRESS", "RETRY"})
_TRANSIENT_CODES = frozenset({429, 502, 503, 504})


class ZincApiError(RuntimeError):
    """CartBlanche22 failure with a caller-actionable message."""


class ZincTaskTimeout(ZincApiError):
    """Poll deadline exhausted — names the task uuid for manual re-poll."""

    def __init__(self, task: str, waited_s: float,
                 last_transport_error: str | None = None) -> None:
        self.task = task
        # Review 4711232176#3: a network outage looks like "still computing"
        # without this — name the last transport error class so the caller
        # can tell genuine slow compute from a connectivity problem.
        if last_transport_error:
            cause = (f"the last poll attempt hit a transport error "
                     f"({last_transport_error}) — this may be a connectivity "
                     "problem, not server-side compute time")
        else:
            cause = "the server is likely still computing"
        super().__init__(
            f"ZINC task {task} did not complete within {waited_s:.0f}s — "
            f"{cause}. Re-poll {BASE_URL}/search/result/{task} later, or "
            "retry with a narrower query (smaller dist / fewer ids / lower "
            "count) or a larger timeout_s.")


def _looks_like_html(text: str) -> bool:
    """The CartBlanche22 SPA shell (returned for requests the API router
    does not recognize) instead of JSON."""
    head = text.lstrip()[:300].lower()
    return head.startswith("<!doctype") or head.startswith("<html")


def _body_excerpt(text: str, n: int = 200) -> str:
    excerpt = " ".join(text.split())[:n]
    return excerpt or "<empty body>"


class ZincClient:
    """Synchronous CartBlanche22 client hiding the async submit-poll API.

    ``session``/``sleep``/``clock``/``pace_fn`` are injectable for offline
    tests (same seam style as mcp_servers_common.ratelimit.HostPacer).
    """

    def __init__(self, session: requests.Session | None = None,
                 sleep=time.sleep, clock=time.monotonic, pace_fn=pace,
                 min_interval_s: float = MIN_INTERVAL_S,
                 poll_interval_s: float = POLL_INTERVAL_S) -> None:
        if session is None:
            session = requests.Session()
            session.headers.setdefault(
                "User-Agent", "operon-mcp-zinc/0.1 (bundled MCP connector)")
        self.session = session
        self._sleep = sleep
        self._clock = clock
        self._pace = pace_fn
        self.min_interval_s = min_interval_s
        self.poll_interval_s = poll_interval_s

    def _remaining(self, deadline: float) -> float:
        return max(0.0, deadline - self._clock())

    def _http_timeout(self, deadline: float) -> float:
        # Per-request transport timeout, clamped to the remaining overall
        # budget so a slow socket can't run past the deadline. Floor at 1s:
        # requests rejects 0, and a sub-second budget is already exhausted.
        return max(1.0, min(HTTP_TIMEOUT_S, self._remaining(deadline)))

    # ── submit ───────────────────────────────────────────────────────────

    def _submit(self, endpoint: str, data: dict, deadline: float) -> str:
        """POST form fields to a search endpoint; return the task uuid.

        Bounded by ``deadline`` (review 3415624590): Retry-After backoffs
        and per-request timeouts are clamped against the remaining overall
        budget so the submit phase cannot escape it.
        """
        url = f"{BASE_URL}/{endpoint}"
        failure = "no attempt made"
        for attempt in range(SUBMIT_RETRIES + 1):
            if attempt > 0 and self._remaining(deadline) <= 0:
                failure += " (overall timeout budget exhausted during submit)"
                break
            self._pace(url, self.min_interval_s)
            try:
                resp = self.session.post(url, data=data,
                                         timeout=self._http_timeout(deadline))
            except requests.RequestException as exc:
                # Class name only — transport reprs can embed URLs/params.
                failure = (f"network error talking to {url}: "
                           f"{exc.__class__.__name__}")
                if attempt < SUBMIT_RETRIES:
                    self._sleep(min(2.0 * (attempt + 1),
                                    self._remaining(deadline)))
                    continue
                break

            if resp.status_code == 400:
                raise ZincApiError(
                    f"CartBlanche22 rejected the {endpoint} submission "
                    "(HTTP 400). The API accepts form-encoded POST fields "
                    "only; check the parameter values (SMILES syntax, "
                    "ZINC id / supplier-code format, subset name). Server "
                    f"detail: {_body_excerpt(resp.text)}")
            if resp.status_code in _TRANSIENT_CODES:
                failure = (f"HTTP {resp.status_code} from {endpoint} "
                           "(transient upstream condition)")
                if attempt < SUBMIT_RETRIES:
                    backoff = retry_after_seconds(
                        resp.headers.get("Retry-After"),
                        2.0 * (attempt + 1))
                    self._sleep(min(backoff, self._remaining(deadline)))
                    continue
                break
            if resp.status_code != 200:
                raise ZincApiError(
                    f"CartBlanche22 {endpoint} returned HTTP "
                    f"{resp.status_code}: {_body_excerpt(resp.text)}")

            if _looks_like_html(resp.text):
                raise ZincApiError(
                    f"CartBlanche22 returned its HTML app shell instead of "
                    f"a JSON task receipt for {endpoint} — the request was "
                    "not understood as an API call (this is what happens "
                    "for GET query-string requests or unknown form fields). "
                    f"Form fields sent: {sorted(data)}")
            try:
                payload = resp.json()
            except ValueError:
                raise ZincApiError(
                    f"CartBlanche22 {endpoint} returned a non-JSON body "
                    f"where a task receipt was expected: "
                    f"{_body_excerpt(resp.text)}")
            task = payload.get("task") if isinstance(payload, dict) else None
            if not task:
                raise ZincApiError(
                    f"CartBlanche22 {endpoint} response carried no task id "
                    f"(keys: {sorted(payload) if isinstance(payload, dict) else type(payload).__name__}) "
                    "— the async submit contract may have changed.")
            return str(task)
        raise ZincApiError(
            f"CartBlanche22 {endpoint} submission failed after "
            f"{SUBMIT_RETRIES + 1} attempts: {failure}")

    # ── poll ─────────────────────────────────────────────────────────────

    def _read_capped(self, resp: requests.Response, task: str) -> str:
        """Streamed body read bounded at MAX_RESPONSE_BYTES.

        iter_content yields DECODED bytes, so the cap bounds what actually
        lands in memory — a runaway result fails loudly with a narrow-the-
        query message instead of building a multi-hundred-MB string in the
        one warm process (review 3415652687; same shape as biomart_query's
        max_response_bytes guard).
        """
        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=1 << 20):
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                resp.close()
                raise ZincApiError(
                    f"ZINC task {task} result exceeded "
                    f"{MAX_RESPONSE_BYTES} bytes — narrow the query "
                    "(smaller dist/adist, fewer ids, lower count) and "
                    "retry. The server-side task is complete; re-polling "
                    "will hit the same body.")
            chunks.append(chunk)
        return b"".join(chunks).decode(resp.encoding or "utf-8",
                                       errors="replace")

    def _poll(self, task: str, deadline: float, timeout_s: float) -> dict:
        """Poll /search/result/<task> until completion; return the payload."""
        # Task uuid comes from the server, but quote it anyway — never
        # interpolate unsanitized text into a URL path segment.
        url = f"{BASE_URL}/search/result/{quote(str(task), safe='')}"
        last_transport_error: str | None = None
        while True:
            self._pace(url, self.min_interval_s)
            pending = False
            # The try/except spans the GET *and* the streamed body read
            # (review 3415838646): with stream=True the body downloads
            # lazily inside _read_capped's iter_content loop, so a mid-body
            # ChunkedEncodingError/ConnectionError must be the same
            # transient-poll-miss as a connect-time failure — re-polling the
            # same uuid fetches the same completed result. ZincApiError
            # raised inside the block is a different type and propagates.
            try:
                resp = self.session.get(url, stream=True,
                                        timeout=self._http_timeout(deadline))
                last_transport_error = None
                if resp.status_code in _TRANSIENT_CODES:
                    resp.close()
                    pending = True
                elif resp.status_code != 200:
                    body = self._read_capped(resp, task)
                    raise ZincApiError(
                        f"polling ZINC task {task} returned HTTP "
                        f"{resp.status_code}: {_body_excerpt(body)}")
                else:
                    body = self._read_capped(resp, task)
                    if _looks_like_html(body):
                        raise ZincApiError(
                            f"polling ZINC task {task} returned the HTML app "
                            "shell instead of JSON — the task id was not "
                            "recognized by /search/result/.")
                    try:
                        payload = json.loads(body)
                    except ValueError:
                        raise ZincApiError(
                            f"polling ZINC task {task} returned a non-JSON "
                            f"body: {_body_excerpt(body)}")
                    status = (payload.get("status")
                              if isinstance(payload, dict) else None)
                    if status == "FAILURE":
                        raise ZincApiError(
                            f"ZINC task {task} failed server-side (status "
                            "FAILURE). Check the query parameters (SMILES "
                            "syntax, id formats) and retry; if it persists "
                            "the upstream worker may be unhealthy.")
                    # Ready iff SUCCESS, OR a status-LESS body where the
                    # result key is PRESENT (reviews 3415810984 / 3415949458):
                    # a PENDING/PROGRESS body whose `result` is a placeholder
                    # []/{} keeps polling (`is not None` short-circuited
                    # there); a status-less `{"result": []}` is a real
                    # zero-match completion (the `or truthy` cure for the
                    # first regressed this — `"result" in payload` is the
                    # right gate when no status is sent).
                    if isinstance(payload, dict) and (
                            status == "SUCCESS"
                            or (status is None and "result" in payload)):
                        return payload
                    if status in _PENDING_STATUSES or status is None:
                        pending = True
                    else:
                        raise ZincApiError(
                            f"ZINC task {task} reported unexpected status "
                            f"{status!r}.")
            except requests.RequestException as exc:
                # Transient poll miss (connect-time OR mid-body stream
                # drop); the deadline bounds us. Class name only —
                # transport reprs can embed URLs/params.
                last_transport_error = exc.__class__.__name__
                pending = True
            if pending and self._clock() >= deadline:
                raise ZincTaskTimeout(task, timeout_s, last_transport_error)
            self._sleep(min(self.poll_interval_s, self._remaining(deadline)))

    # ── public surface ───────────────────────────────────────────────────

    def search(self, endpoint: str, data: dict,
               timeout_s: float = DEFAULT_TIMEOUT_S) -> dict[str, list[dict]]:
        """Submit a search and block until its result is available.

        Returns the result as a dict keyed by source database (``zinc22``,
        ``zinc20``), each value a list of record dicts — the upstream shape,
        normalized so absent/odd payloads never leak to tools.

        ``timeout_s`` is the OVERALL submit→result budget (review
        3415624590): the deadline is computed once here and threaded
        through ``_submit`` (whose backoffs are clamped against it) and
        ``_poll`` so neither phase can run past it.
        """
        deadline = self._clock() + timeout_s
        task = self._submit(endpoint, data, deadline)
        payload = self._poll(task, deadline, timeout_s)
        result = payload.get("result")
        if result is None:
            return {}
        if isinstance(result, list):
            # Defensive: some deployments return a bare list (single-source).
            return {"zinc22": [r for r in result if isinstance(r, dict)]}
        if not isinstance(result, dict):
            raise ZincApiError(
                f"ZINC task {task} produced an unrecognized result shape "
                f"({type(result).__name__}) — expected a dict keyed by "
                "source database.")
        return {
            source: [r for r in records if isinstance(r, dict)]
            for source, records in result.items()
            if isinstance(records, list)
        }


def flatten_result(result: dict[str, list[dict]]) -> tuple[list[dict], dict[str, int]]:
    """Flatten a per-source result into one record list, each record tagged
    with its ``source``; zinc22 (current release) first. Returns the records
    and the per-source counts (the disclosure for capped responses)."""
    ordered = [s for s in SOURCE_ORDER if s in result]
    ordered += sorted(set(result) - set(SOURCE_ORDER))
    records: list[dict] = []
    counts: dict[str, int] = {}
    for source in ordered:
        rows = result[source]
        counts[source] = len(rows)
        records.extend({**row, "source": source} for row in rows)
    return records, counts
