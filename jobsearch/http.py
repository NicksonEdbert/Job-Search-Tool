"""Tiny HTTP helpers (stdlib only) plus an offline mode backed by fixture files."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional

USER_AGENT = "internship-finder/0.1 (+https://github.com)"
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "http"


class FetchError(Exception):
    def __init__(self, url: str, status: Optional[int], message: str):
        super().__init__(f"{message} ({url})")
        self.url = url
        self.status = status


def get_json(url: str, timeout: float = 25, retries: int = 2) -> object:
    last: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (404, 410, 400, 401, 403):
                raise FetchError(url, e.code, f"HTTP {e.code}") from None
            last = e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise FetchError(url, None, f"failed after {retries + 1} tries: {last}")


def link_status(url: str, timeout: float = 15) -> str:
    """'ok', 'dead' (404/410) or 'unknown' (network error, blocked, other codes)."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return "ok" if resp.status < 400 else "unknown"
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return "dead"
            if e.code in (405, 403) and method == "HEAD":
                continue  # some sites refuse HEAD; retry with GET
            return "unknown"
        except Exception:
            return "unknown"
    return "unknown"


def fixture_name(url: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", url.lower()).strip("_")[:180] + ".json"


def offline_get_json(fixture_dir: Path = FIXTURE_DIR) -> Callable[[str], object]:
    def _get(url: str, timeout: float = 0, retries: int = 0) -> object:
        path = fixture_dir / fixture_name(url)
        if not path.exists():
            raise FetchError(url, 404, f"no fixture {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    return _get
