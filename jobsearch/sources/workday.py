"""Workday career sites (<tenant>.<wdN>.myworkdayjobs.com/<site>).

The career page itself loads its listings from a JSON endpoint; we use the same one:
  POST /wday/cxs/<tenant>/<site>/jobs          search (paginated)
  GET  /wday/cxs/<tenant>/<site><externalPath>  one posting (full locations, description, date)

Config slug: "<tenant>|<wdN>|<site>", e.g. "mastercard|wd1|CorporateCareers".
"""

import re
from datetime import datetime, timedelta, timezone

from ..filter import relevant_title
from ..models import Job, html_to_text, to_iso

PAGE = 20
MAX_PAGES = 5
MAX_DETAILS = 40
PROMISING = re.compile(r"indonesia|jakarta|tangerang|bekasi|melbourne|victoria|\bvic\b|australia|remote|anywhere|\d+\s+locations", re.I)
CITY_SEARCH = {"jakarta": "intern Indonesia", "melbourne": "Melbourne"}


def _base(slug: str):
    tenant, wd, site = slug.split("|")
    host = f"https://{tenant}.{wd}.myworkdayjobs.com"
    return host, f"{host}/wday/cxs/{tenant}/{site}", site


def posted_from_text(text: str, now: datetime = None):
    """'Posted Today' / 'Posted Yesterday' / 'Posted 3 Days Ago' / 'Posted 30+ Days Ago' → ISO date."""
    now = now or datetime.now(timezone.utc)
    t = (text or "").lower()
    if "today" in t:
        days = 0
    elif "yesterday" in t:
        days = 1
    else:
        m = re.search(r"(\d+)\+?\s*days?", t)
        if not m:
            return None
        days = int(m.group(1)) + (1 if "+" in t else 0)
    return (now - timedelta(days=days)).isoformat(timespec="seconds")


def fetch(company: dict, client) -> list:
    host, api, site = _base(company["slug"])
    searches = company.get("searches") or [CITY_SEARCH[c] for c in company.get("_cities", ("jakarta",)) if c in CITY_SEARCH]
    postings, seen, errors = [], set(), []
    for text in searches:
        got = 0
        for page in range(MAX_PAGES):
            body = {"appliedFacets": {}, "limit": PAGE, "offset": page * PAGE, "searchText": text}
            try:
                data = client.post_json(f"{api}/jobs", body)
            except Exception as e:  # one failing search shouldn't lose the others
                errors.append(e)
                break
            batch = data.get("jobPostings") or []
            got += len(batch)
            for p in batch:
                if p.get("externalPath") not in seen:
                    seen.add(p.get("externalPath"))
                    postings.append(p)
            if len(batch) < PAGE or got >= (data.get("total") or 0):
                break
    if errors and not postings:
        raise errors[0]

    jobs = []
    details = 0
    for p in postings:
        title = (p.get("title") or "").strip()
        path = p.get("externalPath") or ""
        loc = p.get("locationsText") or ""
        if not path or not relevant_title(title):
            continue
        job = Job(
            id=f"workday:{company['slug'].split('|')[0]}:{path.rsplit('_', 1)[-1] or path}",
            title=title, company=company["name"], location=loc,
            url=f"{host}/en-US/{site}{path}", source="workday",
            posted_at=posted_from_text(p.get("postedOn")),
        )
        if PROMISING.search(loc) and details < MAX_DETAILS:
            details += 1
            try:
                info = (client.get_json(f"{api}{path}", polite=True) or {}).get("jobPostingInfo") or {}
            except Exception:  # keep the summary if the detail page fails
                info = {}
            locs = [info.get("location") or ""] + list(info.get("additionalLocations") or [])
            if (info.get("remoteType") or "").lower().startswith(("remote", "fully")):
                locs.append("Remote")
            elif "hybrid" in (info.get("remoteType") or "").lower():
                locs.append("Hybrid")
            if any(locs):
                job.location = "; ".join(dict.fromkeys(x for x in locs if x))
            job.text = html_to_text(info.get("jobDescription") or "")
            job.posted_at = to_iso(info.get("startDate")) or job.posted_at
            job.url = info.get("externalUrl") or job.url
        jobs.append(job)
    return jobs
