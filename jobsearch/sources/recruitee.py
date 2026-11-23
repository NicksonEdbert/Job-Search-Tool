"""Recruitee public offers API: https://<slug>.recruitee.com/api/offers/"""

from ..models import Job, html_to_text, to_iso

API = "https://{slug}.recruitee.com/api/offers/"


def fetch(company: dict, get_json) -> list:
    data = get_json(API.format(slug=company["slug"]))
    jobs = []
    for j in data.get("offers", []):
        if j.get("status") not in (None, "published"):
            continue
        locs = [j.get("city") or "", j.get("location") or "", j.get("country") or ""]
        if j.get("remote"):
            locs.append("Remote")
        if j.get("hybrid"):
            locs.append("Hybrid")
        jobs.append(Job(
            id=f"recruitee:{company['slug']}:{j['id']}",
            title=(j.get("title") or "").strip(),
            company=company["name"],
            location=", ".join(dict.fromkeys(x for x in locs if x)),
            url=j.get("careers_url") or j.get("url") or "",
            source="recruitee",
            posted_at=to_iso(j.get("published_at") or j.get("created_at")),
            text=html_to_text((j.get("description") or "") + " " + (j.get("requirements") or "")),
        ))
    return jobs
