"""Throttled, instrumented HTTP client for the CADD REST API.

The CADD API (https://cadd.gs.washington.edu/api) is a plain GET service:

    /api/v1.0/{version}/{chrom}:{pos}          -> list of per-substitution dicts
    /api/v1.0/{version}/{chrom}:{start}-{end}  -> list-of-lists with header row

It publishes no documented rate limit; this client defaults to a polite
0.5 s minimum interval between requests (<=2 req/s) and retries transient
failures (5xx, timeouts) with exponential backoff.
"""
from __future__ import annotations

import time

import requests

DEFAULT_BASE_URL = "https://cadd.gs.washington.edu/api/v1.0"
USER_AGENT = "bio-tools-cadd-scores/1.0 (anthropic-experimental/bio-tools)"


class CaddApiError(RuntimeError):
    """Base error for CADD API failures."""


class CaddHttpError(CaddApiError):
    """Non-2xx response that survived retries."""

    def __init__(self, status_code: int, url: str, body_snippet: str = ""):
        super().__init__(f"HTTP {status_code} from {url}: {body_snippet[:200]}")
        self.status_code = status_code
        self.url = url


class CaddClient:
    """requests-based client with throttling, retries and instrumentation.

    Counters ``n_requests`` and ``bytes_downloaded`` accumulate over the
    client's lifetime (used by bench/run_bench.py; retried attempts count
    each attempt's downloaded bytes but each *successful* request once).
    """

    def __init__(self,
                 base_url: str = DEFAULT_BASE_URL,
                 min_interval_s: float = 0.5,
                 timeout_s: float = 120.0,
                 max_retries: int = 3,
                 session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.min_interval_s = min_interval_s
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.n_requests = 0
        self.bytes_downloaded = 0
        self._last_request_t = 0.0

    def _throttle(self) -> None:
        wait = self.min_interval_s - (time.monotonic() - self._last_request_t)
        if wait > 0:
            time.sleep(wait)

    def get_json(self, path: str):
        """GET {base_url}/{path} and return parsed JSON.

        Retries 5xx and transport errors with exponential backoff
        (1, 2, 4 s). 4xx raises immediately (the API is not known to use
        4xx for normal queries; unknown versions/positions return 200 []).
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                resp = self.session.get(url, timeout=self.timeout_s)
                self._last_request_t = time.monotonic()
                self.bytes_downloaded += len(resp.content)
                if resp.status_code >= 500:
                    last_exc = CaddHttpError(resp.status_code, url, resp.text)
                    raise last_exc
                if resp.status_code >= 400:
                    raise CaddHttpError(resp.status_code, url, resp.text)
                self.n_requests += 1
                return resp.json()
            except (requests.ConnectionError, requests.Timeout, CaddHttpError) as exc:
                if isinstance(exc, CaddHttpError) and exc.status_code < 500:
                    raise
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        raise CaddApiError(f"request failed after {self.max_retries + 1} attempts: {url}") from last_exc
