"""Throttled, retrying GET client for the Ensembl REST API.

Politeness: one client instance enforces a minimum interval between requests
(default 0.34 s -> <= 3 req/s, well under Ensembl's 15 req/s ceiling) and
retries 429/5xx once, honouring a numeric ``Retry-After`` (capped) so a
single tool call stays inside the MCP transport budget. All endpoints are
keyless GETs against https://rest.ensembl.org with ``Accept:
application/json``.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

import requests

from mcp_servers_common.ratelimit import retry_after_seconds

BASE_URL = "https://rest.ensembl.org"
USER_AGENT = "ensembl-rest/0.1 (bio-tools fleet; python-requests)"


class EnsemblApiError(RuntimeError):
    """Unrecoverable API or transport error (carries the HTTP status)."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass
class TransportStats:
    requests: int = 0
    bytes_downloaded: int = 0


class EnsemblClient:
    """GET client returning parsed JSON payloads."""

    RETRY_STATUSES = {429, 500, 502, 503, 504}

    def __init__(self, base_url: str = BASE_URL, min_interval_s: float = 0.34,
                 timeout_s: float = 12.0, max_retries: int = 1,
                 retry_after_cap_s: float = 10.0,
                 session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.min_interval_s = min_interval_s
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.retry_after_cap_s = retry_after_cap_s
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/json",
                                     "User-Agent": USER_AGENT})
        self.stats = TransportStats()
        self._last_request_t = 0.0

    def _throttle(self) -> None:
        dt = time.monotonic() - self._last_request_t
        if dt < self.min_interval_s:
            time.sleep(self.min_interval_s - dt)

    def get(self, path: str, params: dict | None = None,
            max_retries: int | None = None):
        """GET ``path`` (leading slash) and return the parsed JSON body.

        ``max_retries=0`` disables retries for a call (used when a tool
        chains two upstream requests and must not stack retry budgets).
        Raises EnsemblApiError on non-200 with the upstream ``error``
        message and status attached.
        """
        retries = self.max_retries if max_retries is None else max_retries
        url = self.base_url + path
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            self._throttle()
            try:
                resp = self.session.get(url, params=params or {},
                                        timeout=self.timeout_s)
            except requests.RequestException as exc:
                self._last_request_t = time.monotonic()
                last_err = exc
                if attempt < retries:
                    time.sleep(2.0)
                continue
            self._last_request_t = time.monotonic()
            self.stats.requests += 1
            self.stats.bytes_downloaded += len(resp.content)
            if resp.status_code in self.RETRY_STATUSES and attempt < retries:
                retry_after = resp.headers.get("Retry-After", "")
                delay = retry_after_seconds(retry_after, 2.0,
                                            cap=self.retry_after_cap_s)
                last_err = EnsemblApiError(f"HTTP {resp.status_code}",
                                           resp.status_code)
                time.sleep(delay)
                continue
            if resp.status_code != 200:
                try:
                    message = resp.json().get("error") or resp.text[:300]
                except json.JSONDecodeError:
                    message = resp.text[:300]
                raise EnsemblApiError(
                    f"Ensembl REST {path}: HTTP {resp.status_code}: "
                    f"{message}", resp.status_code)
            try:
                return resp.json()
            except json.JSONDecodeError as exc:
                raise EnsemblApiError(
                    f"Ensembl REST {path}: non-JSON 200 body") from exc
        raise EnsemblApiError(
            f"Ensembl REST {path}: giving up after {retries + 1} attempts: "
            f"{last_err!r}")
