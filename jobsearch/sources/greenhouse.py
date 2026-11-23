"""Greenhouse public job board API: https://developers.greenhouse.io/job-board.html"""

from ..models import Job, html_to_text, to_iso

API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


def fetch(company: dict, get_json) -> list:
    data = get_json(API.format(slug=company["slug"]))
    jobs = []
    for j in data.get("jobs", []):
        offices = [o.get("name", "") for o in j.get("offices") or []]
        location = "; ".join(x for x in [(j.get("location") or {}).get("name", "")] + offices if x)
        jobs.append(Job(
            id=f"greenhouse:{company['slug']}:{j['id']}",
            title=j.get("title", "").strip(),
            company=company["name"],
            location=location,
            url=j.get("absolute_url", ""),
            source="greenhouse",
            posted_at=to_iso(j.get("first_published") or j.get("updated_at")),
            text=html_to_text(j.get("content", "")),
        ))
    return jobs
