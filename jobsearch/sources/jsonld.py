"""Generic career-page reader using Google-for-Jobs structured data.

Many career sites embed each posting as schema.org JobPosting JSON-LD:
  <script type="application/ld+json">{"@type": "JobPosting", "title": ..., "jobLocation": ...}</script>

Config:
  {"name": "...", "ats": "jsonld", "slug": "<listing page URL or sitemap.xml URL>",
   "link_pattern": "optional regex for job-page links on the listing page / sitemap"}

Works in two steps: read the listing page (or sitemap), collect job-page links that look like
internships, then read JobPosting data from each (at most MAX_PAGES, politely).
"""

import json
import re
from urllib.parse import urljoin

from ..filter import relevant_title
from ..models import Job, html_to_text, to_iso

MAX_PAGES = 40
LD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
HREF_RE = re.compile(r'href=["\']([^"\'#]+)["\']', re.I)
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
JOBISH = re.compile(r"/(jobs?|careers?|vacanc|lowongan|karir|position|opening|requisition)", re.I)
INTERNISH = re.compile(r"intern|magang|trainee|graduate|apprentice|pkl|junior|entry|casual|student|volunteer|support|"
                       r"service-?desk|help-?desk|associate", re.I)


def _walk(node):
    if isinstance(node, list):
        for n in node:
            yield from _walk(n)
    elif isinstance(node, dict):
        t = node.get("@type")
        if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
            yield node
        for key in ("@graph", "itemListElement", "item", "mainEntity"):
            if key in node:
                yield from _walk(node[key])


def postings_in(html: str) -> list:
    out = []
    for raw in LD_RE.findall(html or ""):
        try:
            out += list(_walk(json.loads(raw.strip())))
        except json.JSONDecodeError:
            # Some sites put several objects or trailing commas in one block; try a lenient fix.
            try:
                out += list(_walk(json.loads(re.sub(r",\s*([}\]])", r"\1", raw.strip()))))
            except json.JSONDecodeError:
                continue
    return out


def _text(v) -> str:
    if isinstance(v, dict):
        return v.get("name") or v.get("value") or ""
    if isinstance(v, list):
        return ", ".join(_text(x) for x in v)
    return str(v or "")


def location_of(p: dict) -> str:
    parts = []
    locs = p.get("jobLocation") or []
    for loc in locs if isinstance(locs, list) else [locs]:
        addr = (loc or {}).get("address") if isinstance(loc, dict) else None
        if isinstance(addr, dict):
            parts += [addr.get("addressLocality") or "", addr.get("addressRegion") or "", _text(addr.get("addressCountry"))]
        elif isinstance(addr, str):
            parts.append(addr)
    if "TELECOMMUTE" in str(p.get("jobLocationType") or "").upper():
        req = _text(p.get("applicantLocationRequirements"))
        parts.append("Remote" + (f" ({req})" if req else ""))
    return ", ".join(dict.fromkeys(x.strip() for x in parts if x and x.strip()))


def to_job(p: dict, page_url: str, company: dict) -> Job:
    ident = p.get("identifier")
    ident = _text(ident) if isinstance(ident, (dict, list)) else (ident or "")
    url = p.get("url") or page_url
    org = _text(p.get("hiringOrganization")) or company["name"]
    return Job(
        id=f"jsonld:{company['name'].lower()}:{ident or url}",
        title=html_to_text(p.get("title") or "").strip(),
        company=org if company.get("use_org_name") else company["name"],
        location=location_of(p),
        url=url,
        source="careerpage",
        posted_at=to_iso(p.get("datePosted")),
        text=html_to_text(p.get("description") or ""),
    )


def fetch(company: dict, client) -> list:
    start = company["slug"]
    pattern = re.compile(company["link_pattern"], re.I) if company.get("link_pattern") else None
    page = client.get_text(start)
    jobs = [to_job(p, start, company) for p in postings_in(page)]

    if start.endswith(".xml") or "<urlset" in page[:500] or "<sitemapindex" in page[:500]:
        links = LOC_RE.findall(page)
    else:
        links = [urljoin(start, h) for h in HREF_RE.findall(page)]
    links = [u for u in dict.fromkeys(links) if (pattern.search(u) if pattern else JOBISH.search(u))]
    # Only open pages whose URL or link text suggests an internship (keeps requests low).
    candidates = [u for u in links if INTERNISH.search(u)] or ([] if not pattern else links)
    for url in candidates[:MAX_PAGES]:
        try:
            html = client.get_text(url)
        except Exception:
            continue
        found = postings_in(html)
        if found:
            jobs += [to_job(p, url, company) for p in found]
    # De-duplicate by id, keep internship-looking titles only (listing pages can embed every job).
    seen, out = set(), []
    for j in jobs:
        if j.id not in seen and relevant_title(j.title):
            seen.add(j.id)
            out.append(j)
    return out
