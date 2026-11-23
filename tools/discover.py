"""Find which hiring system a company uses, and whether it has Jakarta / remote internships.

    python tools/discover.py gojek traveloka "bank jago"        # try names as board slugs
    python tools/discover.py --file tools/candidates.json         # bulk (slugs, SuccessFactors, Workday, URLs)

Prints one line per board that answered, with total postings, Indonesia postings and
internships in Indonesia. Use the result to add entries to config/companies.json.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobsearch.filter import is_internship  # noqa: E402

UA = "internship-finder/0.2 (job search helper)"
WIDE = False
PLACES = {
    "indonesia": r"jakarta|indonesia|tangerang|bekasi|depok|bogor|\bjkt\b|\bID\b",
    "melbourne": r"melbourne|victoria|\bVIC\b|docklands|southbank|richmond|cremorne|clayton|collingwood",
}
IDN = re.compile(PLACES["indonesia"], re.I)
ENTRY = re.compile(r"\b(intern|internship|graduate|junior|entry|trainee|casual|student|support|service desk|help ?desk|"
                   r"analyst|associate|volunteer)\b", re.I)
SENIOR = re.compile(r"\b(senior|sr\.?|lead|principal|manager|head|director|staff|architect)\b", re.I)


def req(url, data=None, timeout=20):
    headers = {"User-Agent": UA, "Accept": "application/json, text/html, application/xml;q=0.9"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=timeout) as r:
            raw = r.read(40_000_000)
            ct = r.headers.get("Content-Type", "")
            return r.status, raw.decode("utf-8", "replace"), ct
    except urllib.error.HTTPError as e:
        return e.code, "", ""
    except Exception as e:  # noqa: BLE001
        return str(e)[:60], "", ""


def summarize(kind, name, items):
    """items: list of (title, location)."""
    idn = [(t, l) for t, l in items if IDN.search(l or "")]
    interns = [(t, l) for t, l in idn if is_internship(t) or (WIDE and ENTRY.search(t) and not SENIOR.search(t))]
    remote_interns = [(t, l) for t, l in items if is_internship(t) and re.search(r"remote|anywhere|worldwide", l or "", re.I)]
    return {"kind": kind, "name": name, "total": len(items), "indonesia": len(idn), "intern_id": len(interns),
            "intern_remote": len(remote_interns), "samples": [t for t, _ in (interns + remote_interns)[:4]]}


def try_slug(slug):
    out = []
    s, b, _ = req(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    if s == 200 and b:
        js = json.loads(b).get("jobs", [])
        out.append(summarize("greenhouse", slug, [(j["title"], (j.get("location") or {}).get("name", "")) for j in js]))
    s, b, _ = req(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if s == 200 and b.startswith("["):
        js = json.loads(b)
        out.append(summarize("lever", slug, [(j.get("text", ""), " ".join([(j.get("categories") or {}).get("location") or "", j.get("country") or "", j.get("workplaceType") or ""])) for j in js]))
    s, b, _ = req(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    if s == 200 and b:
        js = json.loads(b).get("jobs", [])
        out.append(summarize("ashby", slug, [(j.get("title", ""), f"{j.get('location', '')} {'remote' if j.get('isRemote') else ''}") for j in js]))
    s, b, _ = req(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100")
    if s == 200 and b:
        d = json.loads(b)
        if d.get("totalFound"):
            out.append(summarize("smartrecruiters", slug, [(j.get("name", ""), json.dumps(j.get("location", {}))) for j in d.get("content", [])]))
    s, b, _ = req(f"https://apply.workable.com/api/v1/widget/accounts/{slug}")
    if s == 200 and b:
        js = json.loads(b).get("jobs", [])
        if js:
            out.append(summarize("workable", slug, [(j.get("title", ""), f"{j.get('city', '')} {j.get('country', '')} {'remote' if j.get('telecommuting') else ''}") for j in js]))
    s, b, _ = req(f"https://{slug}.recruitee.com/api/offers/")
    if s == 200 and b:
        js = json.loads(b).get("offers", [])
        if js:
            out.append(summarize("recruitee", slug, [(j.get("title", ""), f"{j.get('location', '')} {j.get('country', '')} {'remote' if j.get('remote') else ''}") for j in js]))
    s, b, _ = req(f"https://{slug}.teamtailor.com/jobs.rss")
    if s == 200 and "<item>" in b:
        titles = re.findall(r"<item>.*?<title>(.*?)</title>", b, re.S)
        out.append(summarize("teamtailor", slug, [(t, b) for t in titles]))
    return out


def try_successfactors(domain):
    """SAP SuccessFactors career sites: search page lists /job/<Location>-<Title>/<id>/ links."""
    s, b, _ = req(f"https://{domain}/search/?q=intern&locationsearch=Indonesia")
    if s != 200 or not b:
        return [{"kind": "successfactors", "name": domain, "error": s}]
    links = re.findall(r'href="(/[^"]*?/job/[^"]+?/\d+/)"[^>]*>\s*([^<]+?)\s*<', b)
    if not links:
        links = re.findall(r'href="(/job/[^"]+?/\d+/)"[^>]*>\s*([^<]+?)\s*<', b)
    items = [(t, p) for p, t in dict.fromkeys(links)]
    r = summarize("successfactors", domain, items)
    s2, b2, _ = req(f"https://{domain}/sitemap.xml")
    r["sitemap"] = s2
    return [r]


def try_workday(spec):
    """spec: tenant|wdN|site"""
    tenant, wd, site = spec.split("|")
    url = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    s, b, _ = req(url, data={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "intern Indonesia"})
    if s != 200 or not b:
        return [{"kind": "workday", "name": spec, "error": s}]
    d = json.loads(b)
    items = [(j.get("title", ""), j.get("locationsText", "")) for j in d.get("jobPostings", [])]
    r = summarize("workday", spec, items)
    r["total_search"] = d.get("total")
    return [r]


def try_workday_tenant(tenant):
    """Find a company's Workday career site(s) without knowing the site name: look at where the root redirects."""
    out = []
    for wd in ("wd1", "wd3", "wd5", "wd10", "wd12", "wd102", "wd103", "wd105"):
        host = f"https://{tenant}.{wd}.myworkdayjobs.com"
        try:
            with urllib.request.urlopen(urllib.request.Request(host + "/", headers={"User-Agent": UA}), timeout=15) as r:
                final, body = r.geturl(), r.read(400_000).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        sites = set(re.findall(r"myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)", final))
        sites |= set(re.findall(r'(?:href|content)="/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]{3,})/?(?:job|login)?["/]', body))
        sites -= {"wday", "en-US", "static", "assets"}
        for site in list(sites)[:4]:
            out += try_workday(f"{tenant}|{wd}|{site}")
        if sites:
            break
    return out or [{"kind": "workday-tenant", "name": tenant, "error": "no site found"}]


def try_url(url):
    """Any career page: count JobPosting JSON-LD blocks and job-looking links."""
    s, b, ct = req(url)
    if s != 200:
        return [{"kind": "url", "name": url, "error": s}]
    ld = len(re.findall(r'"@type"\s*:\s*"JobPosting"', b))
    return [{"kind": "url", "name": url, "content_type": ct[:40], "jsonld_jobposting": ld,
             "intern_mentions": len(re.findall(r"\bintern(ship)?\b|\bmagang\b", b, re.I)), "bytes": len(b)}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--where", default="indonesia", help="indonesia | melbourne | any regex")
    ap.add_argument("--wide", action="store_true", help="count entry-level/casual/student roles, not just internships")
    a = ap.parse_args()
    global IDN, WIDE
    IDN = re.compile(PLACES.get(a.where, a.where), re.I)
    WIDE = a.wide
    cand = {"slugs": [], "successfactors": [], "workday": [], "urls": [], "workday_tenants": []}
    if a.file:
        cand.update(json.loads(Path(a.file).read_text()))
    for n in a.names:
        base = re.sub(r"[^a-z0-9]", "", n.lower())
        cand["slugs"] += list(dict.fromkeys([base, n.lower().replace(" ", "-")]))
    jobs = [(try_slug, s) for s in dict.fromkeys(cand["slugs"])]
    jobs += [(try_successfactors, d) for d in cand["successfactors"]]
    jobs += [(try_workday, w) for w in cand["workday"]]
    jobs += [(try_url, u) for u in cand["urls"]]
    jobs += [(try_workday_tenant, t) for t in cand["workday_tenants"]]
    def safe(fj):
        try:
            return fj[0](fj[1])
        except Exception as e:  # noqa: BLE001
            return [{"kind": fj[0].__name__, "name": str(fj[1]), "error": f"crash: {e}"[:120]}]

    with cf.ThreadPoolExecutor(12) as ex:
        for res in ex.map(safe, jobs):
            for r in res:
                if r.get("error") is not None:
                    print("MISS", json.dumps(r), flush=True)
                elif r.get("total") or r.get("jsonld_jobposting") or r.get("kind") == "url":
                    print("HIT ", json.dumps(r, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
