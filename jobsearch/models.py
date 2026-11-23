"""The normalized job record every source returns."""

from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Job:
    id: str  # "<ats>:<company slug>:<posting id>", stable across runs
    title: str
    company: str
    location: str
    url: str
    source: str  # ats name, e.g. "greenhouse"
    posted_at: Optional[str] = None  # ISO 8601, UTC
    text: str = ""  # plain-text description (may be empty until details load)
    detail_url: Optional[str] = None  # where to fetch the description if text is empty
    # Filled in later by history / ghost / score:
    first_seen: Optional[str] = None
    is_new: bool = False
    reposts: int = 0
    ghost_risk: str = "low"
    ghost_reasons: list = field(default_factory=list)
    category: str = "other"  # "cyber" | "tech" | "other"
    timing: str = "unknown"  # "good" | "check" | "long" | "later" | "unknown"
    flags: list = field(default_factory=list)
    score: int = 0

    def to_dict(self, text_limit: int = 4000) -> dict:
        d = asdict(self)
        d.pop("detail_url", None)
        d["text"] = (self.text or "")[:text_limit]
        return d


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")


def html_to_text(raw: str) -> str:
    """Rough HTML → plain text (unescapes twice: Greenhouse double-escapes)."""
    if not raw:
        return ""
    s = html.unescape(html.unescape(raw))
    s = re.sub(r"(?i)<\s*(br|/p|/li|/h\d|/div)\s*/?>", "\n", s)
    s = _TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def to_iso(value) -> Optional[str]:
    """Accept ISO strings or epoch milliseconds; return ISO 8601 in UTC."""
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            dt = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (ValueError, OverflowError, OSError):
        return None


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
