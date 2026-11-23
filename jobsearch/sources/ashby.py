"""Ashby public job board API: https://developers.ashbyhq.com/docs/public-job-posting-api"""

from ..models import Job, to_iso

API = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


def fetch(company: dict, get_json) -> list:
    data = get_json(API.format(slug=company["slug"]))
    jobs = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j.get("location") or ""]
        locs += [s.get("location", "") for s in j.get("secondaryLocations") or [] if isinstance(s, dict)]
        addr = ((j.get("address") or {}).get("postalAddress") or {})
        locs += [addr.get("addressLocality") or "", addr.get("addressCountry") or ""]
        jobs.append(Job(
            id=f"ashby:{company['slug']}:{j['id']}",
            title=(j.get("title") or "").strip(),
            company=company["name"],
            location="; ".join(dict.fromkeys(x for x in locs if x)),
            url=j.get("jobUrl", ""),
            source="ashby",
            posted_at=to_iso(j.get("publishedAt")),
            text=(j.get("descriptionPlain") or "").strip(),
        ))
    return jobs
