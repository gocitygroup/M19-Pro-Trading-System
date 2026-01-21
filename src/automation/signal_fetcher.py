from __future__ import annotations

import json
import logging
import os
import time
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from src.automation.models import Signal, parse_signals

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchConfig:
    """
    Minimal, config-driven fetcher settings.

    Environment variables (optional):
    - GSIGNALX_SIGNALS_URL: full URL to signals endpoint
    - GSIGNALX_SIGNALS_PATH: if GSIGNALX_SIGNALS_URL is host-only, append this path (default /api/third-party/signals)
    - GSIGNALX_API_KEY: bearer token (if required)
    - GSIGNALX_AUTH_MODE: bearer|x_api_key|header|query|none (default bearer)
    - GSIGNALX_AUTH_HEADER_NAME: header name for header mode (default Authorization)
    - GSIGNALX_AUTH_HEADER_PREFIX: prefix for header mode (default Bearer )
    - GSIGNALX_AUTH_QUERY_PARAM: query param for query mode (default api_key)
    - GSIGNALX_TIMEOUT_SECONDS: request timeout (default 15)
    - GSIGNALX_MAX_RETRIES: per-cycle retries (default 3)
    - GSIGNALX_BACKOFF_SECONDS: base backoff (default 1.0)
    - GSIGNALX_PAGE_SIZE: pagination page size (default 200)
    - GSIGNALX_PAGE_PARAM: page param name (default page)
    - GSIGNALX_PAGE_SIZE_PARAM: page size param name (default limit)
    - GSIGNALX_MAX_PAGES: safety cap (default 50)
    """

    signals_url: Optional[str]
    api_key: Optional[str]
    auth_mode: str = "bearer"
    auth_header_name: str = "Authorization"
    auth_header_prefix: str = "Bearer "
    auth_query_param: str = "api_key"
    timeout_seconds: float = 15.0
    max_retries: int = 3
    backoff_seconds: float = 1.0
    page_size: int = 200
    page_param: str = "page"
    page_size_param: str = "limit"
    max_pages: int = 50


def load_fetch_config_from_env() -> FetchConfig:
    def _get_first(*names: str) -> Optional[str]:
        for n in names:
            v = os.getenv(n)
            if v and str(v).strip():
                return str(v).strip()
        return None

    def _get_int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except Exception:
            return default

    def _get_float(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, str(default)))
        except Exception:
            return default

    def _normalize_signals_url(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        url = url.strip()
        # If user provided just host/port (or "/" path), append a default API path
        # matching apitest.py (can be overridden).
        try:
            parsed = urlparse(url)
            path = parsed.path or ""
            if path in ("", "/"):
                default_path = (os.getenv("GSIGNALX_SIGNALS_PATH", "/api/third-party/signals") or "/api/third-party/signals").strip()
                if not default_path.startswith("/"):
                    default_path = "/" + default_path
                return url.rstrip("/") + default_path
        except Exception:
            pass
        return url

    return FetchConfig(
        # Support a few common aliases to reduce config friction.
        signals_url=_normalize_signals_url(_get_first(
            "GSIGNALX_SIGNALS_URL",
            "GSIGNALX_API_URL",
            "GSIGNALX_URL",
            "SIGNALS_URL",
        )),
        api_key=_get_first(
            "GSIGNALX_API_KEY",
            "GSIGNALX_TOKEN",
            "GSIGNALX_BEARER_TOKEN",
        ),
        auth_mode=(os.getenv("GSIGNALX_AUTH_MODE", "bearer") or "bearer").strip().lower(),
        auth_header_name=(os.getenv("GSIGNALX_AUTH_HEADER_NAME", "Authorization") or "Authorization").strip(),
        auth_header_prefix=(os.getenv("GSIGNALX_AUTH_HEADER_PREFIX", "Bearer ") or "Bearer "),
        auth_query_param=(os.getenv("GSIGNALX_AUTH_QUERY_PARAM", "api_key") or "api_key").strip(),
        timeout_seconds=_get_float("GSIGNALX_TIMEOUT_SECONDS", 15.0),
        max_retries=_get_int("GSIGNALX_MAX_RETRIES", 3),
        backoff_seconds=_get_float("GSIGNALX_BACKOFF_SECONDS", 1.0),
        page_size=_get_int("GSIGNALX_PAGE_SIZE", 200),
        page_param=(os.getenv("GSIGNALX_PAGE_PARAM", "page") or "page").strip(),
        page_size_param=(os.getenv("GSIGNALX_PAGE_SIZE_PARAM", "limit") or "limit").strip(),
        max_pages=_get_int("GSIGNALX_MAX_PAGES", 50),
    )


class SignalFetcher:
    """
    Fetches signals from the GSignalX API.

    Pagination is implemented defensively to support common shapes:
    - list response (no pagination)
    - dict with {data/results/items: [...], next: <url>|None}
    - dict with {page, total_pages} and a 'page' query param

    This mirrors typical API test client behavior while remaining schema-safe.
    """

    def __init__(self, config: FetchConfig):
        self.config = config
        self._session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "GSignalX-AutomationRunner/1.0",
        }
        api_key = (self.config.api_key or "").strip()
        mode = (self.config.auth_mode or "bearer").strip().lower()
        if not api_key or mode == "none":
            return headers

        if mode == "bearer":
            # Allow users to provide either a raw token or a full "Bearer <token>" value.
            if api_key.lower().startswith("bearer "):
                headers["Authorization"] = api_key
            else:
                headers["Authorization"] = f"Bearer {api_key}"
            return headers

        if mode == "x_api_key":
            headers["X-API-KEY"] = api_key
            return headers

        if mode == "header":
            name = (self.config.auth_header_name or "Authorization").strip() or "Authorization"
            prefix = self.config.auth_header_prefix or ""
            headers[name] = f"{prefix}{api_key}"
            return headers

        # query mode handled in _page_params()
        return headers

    def fetch_all(self) -> Tuple[List[Signal], Dict[str, Any]]:
        """
        Returns (signals, meta).
        meta includes request diagnostics for UI transparency.
        """
        if not self.config.signals_url:
            raise RuntimeError(
                "GSIGNALX_SIGNALS_URL is not configured. "
                "Set GSIGNALX_SIGNALS_URL or use file mode in the runner."
            )

        start = time.time()
        signals: List[Signal] = []
        pages_fetched = 0

        next_url: Optional[str] = self.config.signals_url
        next_page: Optional[int] = 1

        while next_url and pages_fetched < self.config.max_pages:
            pages_fetched += 1
            payload = self._get_with_retries(next_url, params=self._page_params(next_page))

            page_signals = parse_signals(payload)
            signals.extend(page_signals)

            next_url, next_page = self._detect_next(payload, next_url, next_page)
            if next_url is None:
                break

        meta = {
            "pages_fetched": pages_fetched,
            "signals_count": len(signals),
            "elapsed_seconds": round(time.time() - start, 3),
        }
        return signals, meta

    def load_from_file(self, path: str) -> Tuple[List[Signal], Dict[str, Any]]:
        start = time.time()
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        signals = parse_signals(payload)
        meta = {
            "source": "file",
            "path": path,
            "signals_count": len(signals),
            "elapsed_seconds": round(time.time() - start, 3),
        }
        return signals, meta

    def _page_params(self, page: Optional[int]) -> Dict[str, Any]:
        params: Dict[str, Any] = {self.config.page_size_param or "limit": self.config.page_size}
        if page is not None:
            params[self.config.page_param or "page"] = page

        api_key = (self.config.api_key or "").strip()
        if api_key and (self.config.auth_mode or "").strip().lower() == "query":
            params[self.config.auth_query_param or "api_key"] = api_key
        return params

    def _get_with_retries(self, url: str, params: Optional[Dict[str, Any]]) -> Any:
        last_exc: Optional[BaseException] = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = self._session.get(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=self.config.timeout_seconds,
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:  # requests raises multiple exception types
                last_exc = e
                # If we got an HTTP response, capture a tiny snippet for debugging (no secrets).
                try:
                    status_code = getattr(getattr(e, "response", None), "status_code", None)
                    body = getattr(getattr(e, "response", None), "text", None)
                    if status_code and isinstance(body, str) and body.strip():
                        logger.warning(
                            "HTTP %s response body (first 200 chars): %s",
                            status_code,
                            body.strip()[:200],
                        )
                except Exception:
                    pass
                backoff = self.config.backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Signal fetch failed (attempt %s/%s): %s; backing off %.1fs",
                    attempt,
                    self.config.max_retries,
                    str(e),
                    backoff,
                )
                time.sleep(backoff)
        raise RuntimeError(f"Failed to fetch signals after retries: {last_exc}")

    def _detect_next(
        self, payload: Any, current_url: str, current_page: Optional[int]
    ) -> Tuple[Optional[str], Optional[int]]:
        # No pagination if list
        if isinstance(payload, list):
            return None, None

        if not isinstance(payload, dict):
            return None, None

        # "next" URL style
        next_url = payload.get("next")
        if isinstance(next_url, str) and next_url.strip():
            return next_url.strip(), None

        # "page / total_pages" style
        page = payload.get("page")
        total_pages = payload.get("total_pages") or payload.get("pages")
        try:
            page_i = int(page) if page is not None else None
            total_pages_i = int(total_pages) if total_pages is not None else None
        except Exception:
            page_i = None
            total_pages_i = None

        if page_i and total_pages_i and page_i < total_pages_i:
            return current_url, page_i + 1

        # If the response contains an items list and it's "full", attempt next page.
        items = None
        for key in ("data", "results", "items", "symbols"):
            if key in payload:
                items = payload.get(key)
                break
        if isinstance(items, list) and len(items) >= self.config.page_size:
            if current_page is None:
                return current_url, 2
            return current_url, current_page + 1

        return None, None

