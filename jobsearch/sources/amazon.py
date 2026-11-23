"""Amazon / AWS jobs: the amazon.jobs search page loads results from a public JSON endpoint."""

from datetime import datetime
from urllib.parse import quote

from ..filter import is_internship
from ..models import Job, html_to_text

API = "https://www.amazon.jobs/en/search.json?base_query={q}&loc_query={loc}&result_limit=100&sort=recent"


def _date(s):
    try:
        return datetime.strptime((s or "").strip(), "%B %d, %Y").date().isoformat() + "T00:00:00+00:00"
    except ValueError:
        return None


def fetch(company: dict, get_json) -> list:
    jobs = {}
    for q in company.get("queries", ["intern"]):
        data = get_json(API.format(q=quote(q), loc=quote(company.get("location", "Indonesia"))))
        for j in data.get("jobs", []):
            title = (j.get("title") or "").strip()
            if not is_internship(title):
                continue
            jid = j.get("id_icims") or j.get("id")
            jobs[jid] = Job(
                id=f"amazon:{jid}", title=title, company=j.get("company_name") or "Amazon",
                location="; ".join(x for x in [j.get("normalized_location") or "", j.get("location") or ""] if x),
                url="https://www.amazon.jobs" + (j.get("job_path") or ""), source="amazon",
                posted_at=_date(j.get("posted_date")),
                text=html_to_text(" ".join(j.get(k) or "" for k in ("description", "basic_qualifications",
                                                                     "preferred_qualifications"))),
            )
    return list(jobs.values())
