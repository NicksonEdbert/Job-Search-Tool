"""Job-alert emails: LinkedIn, JobStreet, Glints, Kalibrr and Indeed alerts sent to a dedicated Gmail inbox.

Setup (README): make a Gmail just for alerts, create an app password, point the job sites' alerts at it
(or auto-forward them there), and add the GitHub secrets ALERTS_IMAP_USER / ALERTS_IMAP_PASSWORD.

The inbox is opened READ-ONLY (nothing is deleted, moved or marked read). Only the job's title, company,
location and a clean link (tracking parameters removed) are kept. No email text is stored.
"""

from __future__ import annotations

import email
import email.policy
import imaplib
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from ..models import Job

LOOKBACK_DAYS = 7
MAX_MESSAGES = 400

# (site, regex on a link -> job id, clean URL template)
SITES = [
    ("LinkedIn", re.compile(r"linkedin\.com/(?:comm/)?jobs/view/(?:[^/?\s\"']*?-)?(\d{6,})", re.I),
     "https://www.linkedin.com/jobs/view/{id}/"),
    ("JobStreet", re.compile(r"jobstreet\.(?:com|co\.id)/(?:[a-z]{2}/)?(?:job|lowongan)/(?:[^/?\s\"']*?-)?(\d{6,})", re.I),
     "https://id.jobstreet.com/job/{id}"),
    ("Glints", re.compile(r"glints\.com/(?:[a-z]{2}/)*opportunities/jobs/[^/?\s\"']+/([0-9a-f]{8}-[0-9a-f-]{27})", re.I),
     "https://glints.com/id/opportunities/jobs/job/{id}"),
    ("Kalibrr", re.compile(r"kalibrr\.(?:com|id)/(?:[a-zA-Z-]+/)*c/[^/?\s\"']+/jobs/(\d+)", re.I),
     "https://www.kalibrr.com/c/company/jobs/{id}"),
    ("Indeed", re.compile(r"indeed\.com/(?:rc/clk|viewjob|pagead/clk|m/viewjob)[^\s\"']*?[?&](?:amp;)?jk=([0-9a-f]{16})", re.I),
     "https://id.indeed.com/viewjob?jk={id}"),
]
GENERIC_TEXT = re.compile(
    r"^(view( job| details)?|apply( now)?|lihat( lowongan| detail)?|lamar( sekarang)?|see (job|more)|"
    r"easy apply|more|details|open|\W*)$", re.I)
SEP_RE = re.compile(r"\s+[·•|–—-]\s+")


class _Collector(HTMLParser):
    """Turns an email's HTML into [("link", href, text) | ("text", text)] in reading order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self._href = None
        self._buf = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script", "head"):
            self._skip += 1
        if tag == "a":
            self._flush()
            self._href = dict(attrs).get("href") or ""
        if tag in ("br", "p", "div", "tr", "td", "li", "table", "h1", "h2", "h3", "h4"):
            self._flush()

    def handle_endtag(self, tag):
        if tag in ("style", "script", "head"):
            self._skip = max(0, self._skip - 1)
        if tag == "a":
            text = " ".join(" ".join(self._buf).split())
            self.items.append(("link", self._href or "", text))
            self._href, self._buf = None, []
        elif tag in ("p", "div", "tr", "td", "li", "table", "h1", "h2", "h3", "h4"):
            self._flush()

    def handle_data(self, data):
        if not self._skip:
            self._buf.append(data)

    def _flush(self):
        if self._href is None:
            text = " ".join(" ".join(self._buf).split())
            if text:
                self.items.append(("text", text))
            self._buf = []


def _match(href: str):
    for site, rx, tmpl in SITES:
        m = rx.search(href or "")
        if m:
            return site, m.group(1), tmpl.format(id=m.group(1))
    return None


def parse_html(html: str, received: datetime = None) -> list:
    """Extract jobs from one alert email's HTML. Returns [{site, id, url, title, company, location, received}]."""
    c = _Collector()
    c.feed(html or "")
    c._flush()
    items = c.items
    jobs = {}
    for i, item in enumerate(items):
        if item[0] != "link":
            continue
        hit = _match(item[1])
        if not hit:
            continue
        site, jid, url = hit
        job = jobs.setdefault((site, jid), {"site": site, "id": jid, "url": url, "title": "", "company": "",
                                            "location": "", "received": received})
        text = item[2].strip()
        if text and not GENERIC_TEXT.match(text) and len(text) > len(job["title"]) and len(text) < 140:
            job["title"] = text
            # Lines right after the title (until the next job link) usually hold company and location.
            after = []
            for nxt in items[i + 1:i + 8]:
                if nxt[0] == "link" and _match(nxt[1]):
                    break
                t = nxt[2] if nxt[0] == "link" else nxt[1]
                if t and not GENERIC_TEXT.match(t):
                    after.append(t)
            parts = []
            for line in after[:3]:
                parts += [p.strip() for p in SEP_RE.split(line) if p.strip()]
            if parts:
                job["company"] = parts[0][:80]
            loc = next((p for p in parts[1:] if re.search(r"jakarta|indonesia|remote|hybrid|tangerang|bekasi|"
                                                          r"depok|bogor|on-?site|wfh|selatan|barat|timur|utara|pusat",
                                                          p, re.I)), "")
            job["location"] = loc[:80]
    return [j for j in jobs.values() if j["title"]]


def _html_of(msg) -> str:
    parts = []
    for part in msg.walk():
        ctype = part.get_content_type()
        if ctype == "text/html":
            parts.append(part.get_content())
        elif ctype == "text/plain" and not parts:
            # Plain-text alerts: turn bare URLs into links so the same parser works.
            txt = part.get_content()
            parts.append(re.sub(r"(https?://\S+)", r'<a href="\1">\1</a><br>', txt.replace("\n", "<br>")))
    return "\n".join(parts)


def read_inbox(user: str, password: str, host: str = "imap.gmail.com", days: int = LOOKBACK_DAYS,
               imap_cls=imaplib.IMAP4_SSL) -> list:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%d-%b-%Y")
    found = []
    conn = imap_cls(host)
    try:
        conn.login(user, password)
        conn.select("INBOX", readonly=True)
        typ, data = conn.search(None, "SINCE", since)
        ids = (data[0] or b"").split()[-MAX_MESSAGES:] if typ == "OK" else []
        for mid in ids:
            typ, msg_data = conn.fetch(mid, "(BODY.PEEK[])")
            if typ != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue
            msg = email.message_from_bytes(msg_data[0][1], policy=email.policy.default)
            try:
                received = parsedate_to_datetime(msg["Date"])
            except (TypeError, ValueError):
                received = None
            found += parse_html(_html_of(msg), received)
    finally:
        try:
            conn.logout()
        except Exception:
            pass
    return found


def to_jobs(found: list, company: dict) -> list:
    best = {}
    for f in found:
        key = (f["site"], f["id"])
        if key not in best or (f["received"] and best[key]["received"] and f["received"] < best[key]["received"]):
            best[key] = f  # keep the earliest email that mentioned it
    jobs = []
    for f in best.values():
        received = f["received"].astimezone(timezone.utc).isoformat(timespec="seconds") if f["received"] else None
        job = Job(id=f"alert:{f['site'].lower()}:{f['id']}", title=f["title"],
                  company=f["company"] or f"(see {f['site']})",
                  location=f["location"] or company.get("assume_location", "Jakarta (from alert search)"),
                  url=f["url"], source=f"{f['site'].lower()}-alert", posted_at=received)
        if not f["location"]:
            job.flags.append(f"Location not in the {f['site']} email; assumed from the alert's search")
        jobs.append(job)
    return jobs


class NotConfigured(Exception):
    pass


def fetch(company: dict, client=None, env=os.environ, imap_cls=imaplib.IMAP4_SSL) -> list:
    user, password = env.get("ALERTS_IMAP_USER"), env.get("ALERTS_IMAP_PASSWORD")
    if not (user and password):
        raise NotConfigured("not set up yet (add ALERTS_IMAP_USER / ALERTS_IMAP_PASSWORD secrets, see README)")
    found = read_inbox(user, password.replace(" ", ""), company.get("slug") or "imap.gmail.com", imap_cls=imap_cls)
    return to_jobs(found, company)
