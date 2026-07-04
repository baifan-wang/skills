"""Throttled, retrying GET client for the OpenAlex REST API.

Authentication: OpenAlex requires an ``api_key`` query parameter on EVERY
request (since 2026-02-13; the anonymous polite pool and the ``mailto``
parameter are retired — this client sends NO mailto, in the query or the
User-Agent). The key is resolved lazily per request from the constructor
arg or the ``OPENALEX_API_KEY`` env (injected at spawn by the CLI from the
user's stored OpenAlex credential); a missing key raises
``OpenAlexKeyRequired`` so the tool layer can return a structured
``openalex_key_required`` result instead of a server crash.

Pacing/budget discipline (MCP transport allows < 60 s per tool call): one
client instance enforces a minimum interval between requests (default
0.5 s -> <= 2 req/s), request timeout 20 s, at most ONE retry on transient
5xx/transport errors (Retry-After honored, capped at 10 s). 401/403/409 (key
rejected / key required) and 429 (daily usage budget exhausted) are
terminal with actionable messages — retrying cannot help within a call.
"""
from __future__ import annotations

import json
import time

import requests

from mcp_servers_common.ratelimit import retry_after_seconds
from mcp_servers_common.ua import (OpenAlexKeyRequired, product_ua,
                                   require_openalex_key)

BASE_URL = "https://api.openalex.org"
# No mailto in the UA either — include_email=False keeps the consented
# address out of every OpenAlex request byte (the polite pool is retired).
USER_AGENT = product_ua("openalex-works", include_email=False)


def _scrub_key(text: str, key: str) -> str:
    """Redact the api_key (raw + percent-encoded, incl. double-encoded)
    from any upstream/proxy text bound for a model-visible error — error
    pages can echo the request URI, which carries ``?api_key=``. Callers
    scrub a window much wider than the emitted snippet, THEN truncate —
    truncating first can cut the echoed key mid-way, leaving an
    unmatchable prefix (a 4096-char window vs a <=300-char snippet keeps
    any key that could reach the snippet fully inside the scrub)."""
    if not key or len(key) < 6:
        return text
    from urllib.parse import quote
    for form in (quote(quote(key, safe="")), quote(key, safe=""), key):
        text = text.replace(form, "[redacted]")
    return text


class OpenAlexApiError(RuntimeError):
    """Unrecoverable API or transport error."""


class NotFound(OpenAlexApiError):
    """The API returned 404 for the requested entity."""


class OpenAlexClient:
    """GET client returning parsed JSON bodies."""

    RETRY_STATUSES = {500, 502, 503, 504}

    def __init__(self, base_url: str = BASE_URL, api_key: str | None = None,
                 min_interval_s: float = 0.5, timeout_s: float = 20.0,
                 max_attempts: int = 2,
                 session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        # Constructor override > env. Resolved lazily in get() so importing
        # (and constructing at server start) never fails — the key-required
        # message must reach the agent as a clean tool result.
        self._api_key = api_key
        self.min_interval_s = min_interval_s
        self.timeout_s = timeout_s
        self.max_attempts = max_attempts
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._last_request_t = 0.0

    def _throttle(self) -> None:
        dt = time.monotonic() - self._last_request_t
        if dt < self.min_interval_s:
            time.sleep(self.min_interval_s - dt)

    def _resolve_key(self) -> str:
        # Constructor override > the shared env resolver (which owns the
        # single copy of the user-facing remediation message).
        return self._api_key or require_openalex_key()

    def get(self, path: str, params: dict | None = None) -> dict:
        """GET ``base_url + path``; return the parsed JSON dict.

        Raises OpenAlexKeyRequired when no key is available, NotFound on
        404, OpenAlexApiError on other HTTP errors or after exhausting the
        single retry on 5xx/transport failures. 401/403/409/429 are
        terminal with actionable messages (key rejected / key required /
        daily budget exhausted) — never retried, and the key value never
        appears in an error message (only status + a body snippet).
        """
        q = dict(params or {})
        q["api_key"] = self._resolve_key()
        url = f"{self.base_url}{path}"
        last_err: Exception | None = None
        for attempt in range(self.max_attempts):
            self._throttle()
            try:
                resp = self.session.get(url, params=q, timeout=self.timeout_s)
            except requests.RequestException as exc:
                self._last_request_t = time.monotonic()
                last_err = exc
                if attempt < self.max_attempts - 1:  # no dead sleep on the final attempt (#2875 review 3386234809)
                    time.sleep(2.0)
                continue
            self._last_request_t = time.monotonic()
            if resp.status_code == 404:
                raise NotFound(f"not found: {path}")
            if resp.status_code == 401:
                raise OpenAlexApiError(
                    "HTTP 401: OpenAlex rejected the API key. Re-check it "
                    "under Customize → Credentials → OpenAlex against "
                    "https://openalex.org/settings/api (keys are free "
                    "with an OpenAlex account)."
                )
            if resp.status_code == 403:
                # OpenAlex uses 403 BOTH for auth refusals and for invalid
                # query parameters ("Invalid query parameters error.") —
                # surface the (scrubbed) body so the two are tellable apart.
                # Canonical status matrix: core/src/ops/credentialAsk.ts.
                raise OpenAlexApiError(
                    "HTTP 403: OpenAlex refused the request — either the "
                    "API key was rejected (re-check it under Customize → "
                    "Credentials → OpenAlex) or a query parameter is "
                    f"invalid. Upstream said: "
                    f"{_scrub_key(resp.text[:4096], q.get('api_key') or '')[:200]}"
                )
            if resp.status_code == 409:
                # OpenAlex's keyless/over-budget refusal for anonymous
                # callers — with a key present this means the key was not
                # accepted for this request.
                raise OpenAlexApiError(
                    "HTTP 409: OpenAlex requires a valid API key for this "
                    "request. Re-check the key under Customize → "
                    "Credentials → OpenAlex (free at "
                    "https://openalex.org/settings/api)."
                )
            if resp.status_code == 429:
                raise OpenAlexApiError(
                    "HTTP 429: the OpenAlex API key is over its usage "
                    "limit — most commonly the daily budget is exhausted "
                    "(resets at 00:00 UTC; raise it at "
                    "https://openalex.org/settings/api). If this appeared "
                    "mid-burst, several processes may share the key — "
                    "retry after a pause instead of immediately."
                )
            if resp.status_code in self.RETRY_STATUSES:
                last_err = OpenAlexApiError(
                    f"HTTP {resp.status_code}: "
                    f"{_scrub_key(resp.text[:4096], q.get('api_key') or '')[:200]}")
                # Honor Retry-After like every other fleet client (bounded
                # so the whole tool call stays < 50 s).
                delay = retry_after_seconds(
                    resp.headers.get("Retry-After", ""), 2.0, cap=10.0)
                if attempt < self.max_attempts - 1:  # no dead sleep on the final attempt (#2875 review 3386234809)
                    time.sleep(delay)
                continue
            if resp.status_code != 200:
                raise OpenAlexApiError(
                    f"HTTP {resp.status_code}: "
                    f"{_scrub_key(resp.text[:4096], q.get('api_key') or '')[:300]}")
            try:
                return resp.json()
            except json.JSONDecodeError as exc:
                last_err = exc
                if attempt < self.max_attempts - 1:  # no dead sleep on the final attempt (#2875 review 3386234809)
                    time.sleep(2.0)
                continue
        # requests/urllib3 exception reprs embed the full request URL —
        # including api_key= — so scrub the key (raw + percent-encoded)
        # before it can reach a model-visible tool error.
        detail = _scrub_key(repr(last_err), q.get("api_key") or "")
        raise OpenAlexApiError(
            f"giving up after {self.max_attempts} attempts: {detail}")
