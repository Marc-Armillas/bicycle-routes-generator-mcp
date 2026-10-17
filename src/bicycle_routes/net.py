"""Shared HTTP client: own User-Agent, per-server rate limiting, retries and on-disk cache.

Public services (Nominatim, Overpass, brouter.de) ask clients to identify themselves,
avoid bursts and cache results; every request goes through here.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

# Minimum interval between requests to each public server (seconds).
PUBLIC_INTERVALS = {
    "nominatim.openstreetmap.org": 1.1,
    "brouter.de": 1.0,
    "overpass-api.de": 1.0,
    "api.openrouteservice.org": 1.6,  # 40 requests/min on the free plan
}

TRANSIENT_STATUS = {429, 502, 503, 504}
RETRY_DELAYS = (3.0, 10.0)  # seconds before the 2nd and 3rd attempt


class NetworkError(RuntimeError):
    pass


class HttpClient:
    def __init__(
        self,
        user_agent: str,
        cache_dir: Path | None = None,
        intervals: dict[str, float] | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 90.0,
    ) -> None:
        self.cache_dir = cache_dir
        self.intervals = PUBLIC_INTERVALS if intervals is None else intervals
        self._last_request: dict[str, float] = {}
        self.request_count = 0
        self._client = httpx.Client(
            headers={"User-Agent": user_agent}, timeout=timeout, transport=transport, follow_redirects=True
        )

    # -- cache ---------------------------------------------------------------
    def _cache_file(self, namespace: str, key: str) -> Path | None:
        if self.cache_dir is None:
            return None
        digest = hashlib.sha256(key.encode()).hexdigest()[:32]
        return self.cache_dir / "cache" / namespace / f"{digest}.json"

    def _read_cache(self, path: Path | None, ttl_s: float) -> Any | None:
        if path is None or not path.exists():
            return None
        if time.time() - path.stat().st_mtime > ttl_s:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _write_cache(self, path: Path | None, data: Any) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    # -- rate limiting ---------------------------------------------------------
    def _wait_turn(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        interval = self.intervals.get(host, 0.0)
        if interval <= 0:
            return
        wait = self._last_request.get(host, 0.0) + interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_request[host] = time.monotonic()

    # -- requests --------------------------------------------------------------
    def request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cache_namespace: str | None = None,
        ttl_s: float = 7 * 24 * 3600,
    ) -> Any:
        # Headers (e.g. API keys) are deliberately not part of the cache key.
        key = json.dumps([method, url, params, json_body, data], sort_keys=True, ensure_ascii=False)
        cache_path = self._cache_file(cache_namespace, key) if cache_namespace else None
        cached = self._read_cache(cache_path, ttl_s)
        if cached is not None:
            return cached

        host = urlsplit(url).hostname
        for delay in (*RETRY_DELAYS, None):
            self._wait_turn(url)
            self.request_count += 1
            try:
                response = self._client.request(method, url, params=params, json=json_body, data=data, headers=headers)
            except httpx.HTTPError as e:
                if delay is None:
                    raise NetworkError(f"Could not connect to {host}: {e}") from e
                time.sleep(delay)
                continue
            if response.status_code in TRANSIENT_STATUS and delay is not None:
                time.sleep(delay)
                continue
            break

        if response.status_code >= 400:
            text = response.text.strip().splitlines()[0][:300] if response.text.strip() else ""
            raise NetworkError(f"{host} responded {response.status_code}: {text}")
        try:
            result = response.json()
        except ValueError as e:
            raise NetworkError(f"Invalid response from {host}: {response.text[:300]}") from e
        self._write_cache(cache_path, result)
        return result

    def close(self) -> None:
        self._client.close()
