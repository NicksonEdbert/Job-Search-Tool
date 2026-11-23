"""Lever public postings API: https://github.com/lever/postings-api"""

from ..models import Job, html_to_text, to_iso

API = "https://api.lever.co/v0/postings/{slug}?mode=json"


def fetch(company: dict, get_json) -> list:
    data = get_json(API.format(slug=company["slug"]))
    jobs = []
    for j in data if isinstance(data, list) else []:
        cats = j.get("categories") or {}
        locs = [cats.get("location") or ""] + list(cats.get("allLocations") or [])
        if j.get("country"):
            locs.append(j["country"])
        mode = (j.get("workplaceType") or "").lower()
        if mode in ("remote", "hybrid"):
            locs.append(mode.title())
        location = "; ".join(dict.fromkeys(x for x in locs if x))
        parts = [j.get("descriptionPlain") or ""]
        for lst in j.get("lists") or []:
            parts.append(lst.get("text", ""))
            parts.append(html_to_text(lst.get("content", "")))
        parts.append(j.get("additionalPlain") or "")
        jobs.append(Job(
            id=f"lever:{company['slug']}:{j['id']}",
            title=(j.get("text") or "").strip(),
            company=company["name"],
            location=location,
            url=j.get("hostedUrl", ""),
            source="lever",
            posted_at=to_iso(j.get("createdAt")),
            text="\n".join(p for p in parts if p).strip(),
        ))
    return jobs
