"""Remote-job boards with public JSON feeds. Each job keeps the real employer as `company`.

  remotive  https://remotive.com/api/remote-jobs?search=intern   (asks for attribution: we link to their posting)
  arbeitnow https://www.arbeitnow.com/api/job-board-api            (paginated)
  remoteok  https://remoteok.com/api                               (asks for attribution: we link to their posting)

Only internship titles are kept here; the remote-eligibility check happens in filter.py.
"""

from ..filter import relevant_title as is_internship
from ..models import Job, html_to_text, to_iso


def _remotive(company, get_json):
    jobs = {}
    for term in ("intern", "internship", "trainee"):
        data = get_json(f"https://remotive.com/api/remote-jobs?search={term}")
        for j in data.get("jobs", []):
            if not is_internship(j.get("title", "")):
                continue
            jobs[j["id"]] = Job(
                id=f"remotive:{j['id']}", title=j["title"].strip(), company=j.get("company_name") or "Unknown",
                location=f"Remote ({j.get('candidate_required_location') or 'location not stated'})",
                url=j.get("url", ""), source="remotive", posted_at=to_iso(j.get("publication_date")),
                text=html_to_text(j.get("description") or ""))
    return list(jobs.values())


def _arbeitnow(company, get_json):
    jobs = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    for _ in range(5):
        data = get_json(url)
        for j in data.get("data", []):
            if not is_internship(j.get("title", "")) and "internship" not in [t.lower() for t in j.get("job_types") or []]:
                continue
            loc = j.get("location") or ""
            jobs.append(Job(
                id=f"arbeitnow:{j.get('slug')}", title=(j.get("title") or "").strip(),
                company=j.get("company_name") or "Unknown",
                location=f"Remote ({loc})" if j.get("remote") else loc,
                url=j.get("url", ""), source="arbeitnow",
                posted_at=to_iso((j.get("created_at") or 0) * 1000) if j.get("created_at") else None,
                text=html_to_text(j.get("description") or "")))
        url = (data.get("links") or {}).get("next")
        if not url:
            break
    return jobs


def _remoteok(company, get_json):
    jobs = []
    for j in get_json("https://remoteok.com/api"):
        if not isinstance(j, dict) or "position" not in j or not is_internship(j.get("position", "")):
            continue
        jobs.append(Job(
            id=f"remoteok:{j.get('id')}", title=j["position"].strip(), company=j.get("company") or "Unknown",
            location=f"Remote ({j.get('location') or 'location not stated'})",
            url=j.get("url") or j.get("apply_url") or "", source="remoteok",
            posted_at=to_iso(j.get("date")), text=html_to_text(j.get("description") or "")))
    return jobs


BOARDS = {"remotive": _remotive, "arbeitnow": _arbeitnow, "remoteok": _remoteok}


def fetch(company: dict, get_json) -> list:
    return BOARDS[company["slug"]](company, get_json)
