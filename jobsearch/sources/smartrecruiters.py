"""SmartRecruiters public posting API: https://developers.smartrecruiters.com/docs/posting-api"""

from ..models import Job, html_to_text, to_iso

API = "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={offset}"
MAX_PAGES = 20


def fetch(company: dict, get_json) -> list:
    from . import COUNTRY_NAMES

    jobs = []
    offset = 0
    for _ in range(MAX_PAGES):
        data = get_json(API.format(slug=company["slug"], offset=offset))
        content = data.get("content", [])
        for j in content:
            loc = j.get("location") or {}
            country = (loc.get("country") or "").lower()
            # fullLocation looks like "Jakarta, , Indonesia"; split it and drop blanks/duplicates.
            parts = [p.strip() for p in (loc.get("fullLocation") or "").split(",")]
            parts += [loc.get("city") or "", COUNTRY_NAMES.get(country, country.upper())]
            if loc.get("remote"):
                parts.append("Remote")
            elif loc.get("hybrid"):
                parts.append("Hybrid")
            ident = (j.get("company") or {}).get("identifier") or company["slug"]
            jobs.append(Job(
                id=f"smartrecruiters:{company['slug']}:{j['id']}",
                title=(j.get("name") or "").strip(),
                company=company["name"],
                location=", ".join(dict.fromkeys(p for p in parts if p)),
                url=f"https://jobs.smartrecruiters.com/{ident}/{j['id']}",
                source="smartrecruiters",
                posted_at=to_iso(j.get("releasedDate")),
                detail_url=j.get("ref"),
            ))
        offset += len(content)
        if not content or offset >= data.get("totalFound", 0):
            break
    return jobs


def details(job: Job, get_json) -> None:
    if not job.detail_url:
        return
    d = get_json(job.detail_url)
    sections = ((d.get("jobAd") or {}).get("sections") or {})
    texts = []
    for key in ("jobDescription", "qualifications", "additionalInformation"):
        sec = sections.get(key) or {}
        if sec.get("text"):
            texts.append(f"{sec.get('title', '')}\n{html_to_text(sec['text'])}")
    job.text = "\n".join(texts).strip()
    if d.get("postingUrl"):
        job.url = d["postingUrl"]
    if d.get("active") is False:
        job.flags.append("Posting marked inactive")
