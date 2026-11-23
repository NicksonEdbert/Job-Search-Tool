"""SAP SuccessFactors career sites (e.g. careers.ey.com, jobs.sea.deloitte.com, careers.reckitt.com).

These sites have a public search page:  https://<domain>/search/?q=intern&locationsearch=Indonesia
Each result row links to /job/<Location>-<Title>/<id>/ ; we read the rows, then open internship
postings (politely, robots.txt honoured) for the description and date.

Config slug: the career-site domain. Optional "path_prefix" (e.g. "/ey") if the site lives under a prefix,
and "search" / "location" to override the query (defaults: "intern" / "Indonesia").
"""

import html as htmllib
import re
from datetime import datetime
from urllib.parse import quote, urljoin

from ..filter import relevant_title
from ..models import Job, html_to_text, to_iso

PAGE_SIZE = 25
MAX_PAGES = 4
MAX_DETAILS = 30

ROW_RE = re.compile(r'<tr[^>]*class="[^"]*data-row[^"]*"[^>]*>(.*?)</tr>', re.S | re.I)
LINK_RE = re.compile(r'<a[^>]+href="([^"]*?/job/[^"]+?/\d+/?)"[^>]*>\s*(.*?)\s*</a>', re.S | re.I)
LOC_RE = re.compile(r'class="[^"]*jobLocation[^"]*"[^>]*>(.*?)</', re.S | re.I)
DATE_RE = re.compile(r'class="[^"]*jobDate[^"]*"[^>]*>(.*?)</', re.S | re.I)
DESC_RE = re.compile(r'(?:class="[^"]*jobdescription[^"]*"|itemprop="description")[^>]*>(.*?)</(?:span|div)>\s*</(?:span|div)>',
                     re.S | re.I)
DATEPOSTED_RE = re.compile(r'itemprop="datePosted"[^>]*content="([^"]+)"', re.I)


def _date(text: str):
    t = html_to_text(text or "").strip()
    for fmt in ("%b %d, %Y", "%d %b %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).date().isoformat() + "T00:00:00+00:00"
        except ValueError:
            continue
    return None


def _location_from_path(path: str) -> str:
    # /job/Jakarta-SOC-Analyst-Cybersecurity-12190/1276623901/ -> "Jakarta"
    m = re.search(r"/job/([^/]+)/\d+", path)
    return m.group(1).split("-")[0].replace("%20", " ") if m else ""


def parse_results(html: str, base: str) -> list:
    rows = ROW_RE.findall(html) or [html]
    out, seen = [], set()
    for row in rows:
        for href, title in LINK_RE.findall(row):
            href = htmllib.unescape(href)
            url = urljoin(base, href)
            if url in seen:
                continue
            seen.add(url)
            loc = LOC_RE.search(row) if len(rows) > 1 else None
            date = DATE_RE.search(row) if len(rows) > 1 else None
            out.append({"url": url, "title": html_to_text(title).strip(),
                        "location": html_to_text(loc.group(1)).strip() if loc else _location_from_path(href),
                        "date": _date(date.group(1)) if date else None})
    return out


def fetch(company: dict, client) -> list:
    domain = company["slug"]
    base = f"https://{domain}{company.get('path_prefix', '')}"
    city_search = {"jakarta": ("intern", "Indonesia"), "melbourne": ("", "Melbourne")}
    searches = company.get("searches") or [city_search[c] for c in company.get("_cities", ("jakarta",)) if c in city_search]
    results, errors = [], []
    for q, where in searches:
        for page in range(MAX_PAGES):
            url = (f"{base}/search/?q={quote(q)}&locationsearch={quote(where)}&sortColumn=referencedate"
                   f"&sortDirection=desc&startrow={page * PAGE_SIZE}")
            try:
                batch = parse_results(client.get_text(url), f"https://{domain}")
            except Exception as e:  # one failing search shouldn't lose the others
                errors.append(e)
                break
            new = [r for r in batch if r["url"] not in {x["url"] for x in results}]
            results += new
            if len(batch) < PAGE_SIZE or not new:
                break
    if errors and not results:
        raise errors[0]

    jobs, details = [], 0
    for r in results:
        if not relevant_title(r["title"]):
            continue
        job = Job(id=f"successfactors:{domain}:{r['url'].rstrip('/').rsplit('/', 1)[-1]}", title=r["title"],
                  company=company["name"], location=r["location"], url=r["url"], source="successfactors",
                  posted_at=r["date"])
        if details < MAX_DETAILS:
            details += 1
            try:
                page = client.get_text(r["url"])
                m = DESC_RE.search(page)
                job.text = html_to_text(m.group(1) if m else page)[:8000]
                dp = DATEPOSTED_RE.search(page)
                job.posted_at = job.posted_at or to_iso(dp.group(1)) if dp else job.posted_at
            except Exception:
                pass
        jobs.append(job)
    return jobs
