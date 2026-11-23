"""HTTP client (stdlib only): JSON/HTML/POST, polite fetching, and an offline mode backed by fixture files.

Sources receive a client and may call it like a function (`client(url)` == `client.get_json(url)`),
which keeps the older readers that only need GET-JSON unchanged.
"""

from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

USER_AGENT = "internship-finder/0.2 (personal job-search helper; +https://github.com/NicksonEdbert/Job-Search-Tool)"
ROBOTS_AGENT = "internship-finder"
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "http"


class FetchError(Exception):
    def __init__(self, url: str, status: Optional[int], message: str):
        super().__init__(f"{message} ({url})")
        self.url = url
        self.status = status


def fixture_name(url: str, body: Optional[dict] = None, ext: str = ".json") -> str:
    key = url if body is None else f"POST {url} {json.dumps(body, sort_keys=True)}"
    return re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")[:180] + ext


class Client:
    """Live client. `polite` requests (career pages) honour robots.txt and wait `delay` seconds per host."""

    def __init__(self, delay: float = 1.0, timeout: float = 25, retries: int = 2):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self._robots: dict = {}
        self._next_slot: dict = {}
        self._lock = threading.Lock()

    # -- public API ------------------------------------------------------------------------------
    def __call__(self, url: str, timeout: float = None, retries: int = None):
        return self.get_json(url, timeout=timeout, retries=retries)

    def get_json(self, url: str, timeout: float = None, retries: int = None, polite: bool = False):
        return json.loads(self._request(url, None, "application/json", timeout, retries, polite))

    def post_json(self, url: str, body: dict, timeout: float = None, retries: int = None, polite: bool = True):
        return json.loads(self._request(url, body, "application/json", timeout, retries, polite))

    def get_text(self, url: str, timeout: float = None, retries: int = None, polite: bool = True) -> str:
        return self._request(url, None, "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                             timeout, retries, polite)

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        with self._lock:
            rp = self._robots.get(base)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                raw = self._raw(base + "/robots.txt", None, "text/plain", 15)
                rp.parse(raw.splitlines())
            except FetchError as e:
                # No robots.txt (404) means everything is allowed; other failures: be conservative only on 401/403.
                rp.parse(["User-agent: *", "Disallow: /"] if e.status in (401, 403) else [])
            with self._lock:
                self._robots[base] = rp
        return rp.can_fetch(ROBOTS_AGENT, url)

    # -- internals -------------------------------------------------------------------------------
    def _pace(self, url: str) -> None:
        host = urlsplit(url).netloc
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_slot.get(host, 0.0))
            self._next_slot[host] = slot + self.delay
        if slot > now:
            time.sleep(slot - now)

    def _raw(self, url: str, body: Optional[dict], accept: str, timeout: float) -> str:
        headers = {"User-Agent": USER_AGENT, "Accept": accept, "Accept-Language": "en,id;q=0.8"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read(60_000_000).decode(charset, "replace")
        except urllib.error.HTTPError as e:
            raise FetchError(url, e.code, f"HTTP {e.code}") from None

    def _request(self, url, body, accept, timeout, retries, polite) -> str:
        timeout = timeout or self.timeout
        retries = self.retries if retries is None else retries
        if polite:
            if not self.allowed(url):
                raise FetchError(url, None, "robots.txt disallows this page")
            self._pace(url)
        last: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                return self._raw(url, body, accept, timeout)
            except FetchError as e:
                if e.status in (400, 401, 403, 404, 405, 410, 422):
                    raise
                last = e
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last = e
            time.sleep(1.5 * (attempt + 1))
        raise FetchError(url, None, f"failed after {retries + 1} tries: {last}")


class OfflineClient:
    """Reads responses from tests/fixtures/http/ (see fixture_name). robots.txt honoured if a fixture exists."""

    def __init__(self, fixture_dir: Path = FIXTURE_DIR):
        self.dir = fixture_dir

    def _load(self, url, body=None, ext=".json"):
        path = self.dir / fixture_name(url, body, ext)
        if not path.exists():
            raise FetchError(url, 404, f"no fixture {path.name}")
        return path.read_text(encoding="utf-8")

    def __call__(self, url, timeout=None, retries=None):
        return self.get_json(url)

    def get_json(self, url, timeout=None, retries=None, polite=False):
        return json.loads(self._load(url))

    def post_json(self, url, body, timeout=None, retries=None, polite=True):
        return json.loads(self._load(url, body))

    def get_text(self, url, timeout=None, retries=None, polite=True):
        if polite and not self.allowed(url):
            raise FetchError(url, None, "robots.txt disallows this page")
        return self._load(url, ext=".txt")

    def allowed(self, url):
        parts = urlsplit(url)
        path = self.dir / fixture_name(f"{parts.scheme}://{parts.netloc}/robots.txt", ext=".txt")
        if not path.exists():
            return True
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(path.read_text(encoding="utf-8").splitlines())
        return rp.can_fetch(ROBOTS_AGENT, url)


# Backwards-compatible helpers -----------------------------------------------------------------------
_default = Client()


def get_json(url: str, timeout: float = 25, retries: int = 2):
    return _default.get_json(url, timeout=timeout, retries=retries)


def offline_get_json(fixture_dir: Path = FIXTURE_DIR) -> OfflineClient:
    return OfflineClient(fixture_dir)


def link_status(url: str, timeout: float = 15) -> str:
    """'ok', 'dead' (404/410) or 'unknown' (network error, blocked, other codes)."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return "ok" if resp.status < 400 else "unknown"
        except urllib.error.HTTPError as e:
            if method == "HEAD":
                continue  # many sites answer HEAD with 403/404/405; only trust a GET
            return "dead" if e.code in (404, 410) else "unknown"
        except Exception:
            return "unknown"
    return "unknown"
