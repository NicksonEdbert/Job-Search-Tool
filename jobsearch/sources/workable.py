"""Workable public job widget: https://apply.workable.com/api/v1/widget/accounts/<slug>"""

from ..models import Job, html_to_text, to_iso

API = "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true"


def fetch(company: dict, get_json) -> list:
    data = get_json(API.format(slug=company["slug"]))
    jobs = []
    for j in data.get("jobs", []):
        locs = []
        for loc in j.get("locations") or [{"city": j.get("city"), "country": j.get("country"), "region": j.get("state")}]:
            if isinstance(loc, dict) and not loc.get("hidden"):
                locs += [loc.get("city") or "", loc.get("region") or "", loc.get("country") or ""]
        if j.get("telecommuting"):
            locs.append("Remote")
        if (j.get("workplace") or "").lower() == "hybrid":
            locs.append("Hybrid")
        jobs.append(Job(
            id=f"workable:{company['slug']}:{j.get('shortcode') or j.get('code')}",
            title=(j.get("title") or "").strip(),
            company=company["name"],
            location=", ".join(dict.fromkeys(x for x in locs if x)),
            url=j.get("url") or j.get("shortlink") or "",
            source="workable",
            posted_at=to_iso(j.get("published_on") or j.get("created_at")),
            text=html_to_text(j.get("description") or ""),
        ))
    return jobs
