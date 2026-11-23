"""python -m jobsearch : fetch → filter → history → ghost check → score → write data/."""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from . import digest, ghost, history
from .filter import keep
from .http import Client, FetchError, OfflineClient, link_status
from .sources.email_alerts import NotConfigured
from .score import score
from .sources import SOURCES

ROOT = Path(__file__).resolve().parent.parent


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def fetch_all(companies: list, get_json, workers: int = 8) -> tuple:
    """Return (jobs, source report). A failing board never stops the run."""
    jobs, report = [], []

    def one(c):
        mod = SOURCES.get(c["ats"])
        if mod is None:
            return c, [], f"unknown hiring system '{c['ats']}'"
        try:
            found = mod.fetch(c, get_json)
            for j in found:
                j.origin = c["name"]
            return c, found, None
        except NotConfigured as e:
            return c, [], str(e)
        except FetchError as e:
            return c, [], f"HTTP {e.status}" if e.status else str(e)
        except Exception as e:  # malformed response etc.
            return c, [], f"error: {e}"

    with cf.ThreadPoolExecutor(workers) as ex:
        for c, found, err in ex.map(one, companies):
            report.append({"company": c["name"], "ats": c["ats"], "slug": c.get("slug", ""),
                           "ok": err is None, "postings": len(found), "error": err})
            jobs.extend(found)
    return jobs, report


def load_details(jobs: list, get_json, workers: int = 8) -> None:
    def one(job):
        mod = SOURCES.get(job.source)
        if job.text or not hasattr(mod, "details"):
            return
        try:
            mod.details(job, get_json)
        except Exception as e:
            print(f"  ! could not load details for {job.title} ({job.company}): {e}")

    with cf.ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, jobs))


def dedupe(jobs: list) -> list:
    best = {}
    for j in jobs:
        k = history.role_key(j)
        cur = best.get(k)
        if cur is None or (not cur.text and j.text) or ((j.posted_at or "") > (cur.posted_at or "") and j.text):
            best[k] = j
    return list(best.values())


def write_csv(path: Path, jobs: list) -> None:
    cols = ["score", "category", "title", "company", "location", "posted_at", "ghost_risk", "timing", "flags", "url"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for j in jobs:
            w.writerow([j["score"], j["category"], j["title"], j["company"], j["location"], j["posted_at"] or "",
                        j["ghost_risk"], j["timing"], " | ".join(j["flags"]), j["url"]])


def check_experience_links(out_dir: Path) -> dict:
    items = (load_json(ROOT / "config" / "experience.json", {}) or {}).get("items", [])
    urls = [i["url"] for i in items if i.get("url")]
    with cf.ThreadPoolExecutor(8) as ex:
        status = dict(zip(urls, ex.map(link_status, urls)))
    (out_dir / "experience_status.json").write_text(json.dumps(
        {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "status": status}, indent=1),
        encoding="utf-8")
    return status


def run(args, now: datetime = None, get_json=None) -> dict:
    now = now or datetime.now(timezone.utc)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if get_json is None:
        get_json = OfflineClient() if args.offline else Client()
    companies_path = Path(args.companies or (ROOT / ("tests/fixtures/companies.json" if args.offline else "config/companies.json")))
    companies = [c for c in load_json(companies_path, {"companies": []})["companies"] if c.get("enabled", True)]
    profile = load_json(Path(args.profile), {}) or {}
    extra = tuple(profile.get("extra_places", []))
    include_remote = bool(profile.get("include_remote", True))

    print(f"Fetching {len(companies)} company boards…")
    raw, report = fetch_all(companies, get_json)
    jobs = dedupe([j for j in raw if keep(j, extra, include_remote)])
    load_details(jobs, get_json)

    hist_path = out_dir / "history.json"
    hist = history.load(hist_path)
    first_run = not hist.get("roles")
    fetched = {r["company"] for r in report if r["ok"]}
    closed = history.update(hist, jobs, now=now, fetched_companies=fetched)
    for j in jobs:
        ghost.assess(j, now=now, open_days=history.open_days(hist, j, now))
        score(j, profile, now=now)
    jobs.sort(key=lambda j: -j.score)
    history.save(hist_path, hist)

    rows = [j.to_dict() for j in jobs]
    result = {
        "generated_at": now.isoformat(timespec="seconds"),
        "counts": {"postings_scanned": len(raw), "internships": len(rows),
                   "cyber": sum(r["category"] == "cyber" for r in rows),
                   "tech": sum(r["category"] == "tech" for r in rows),
                   "jakarta": sum(r["where"] in ("jakarta", "indonesia") for r in rows),
                   "remote": sum(r["where"] == "remote" for r in rows),
                   "new": sum(r["is_new"] for r in rows)},
        "sources": sorted(report, key=lambda r: r["company"].lower()),
        "jobs": rows,
        "closed": closed,
    }
    (out_dir / "jobs.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    write_csv(out_dir / "jobs.csv", rows)

    msg = digest.build(rows, first_run=first_run)
    (out_dir / "digest.md").write_text(msg["markdown"], encoding="utf-8")
    if args.send_alert:
        sent = digest.deliver(msg)
        print(f"Alert: {msg['count']} new roles; sent via {', '.join(sent) if sent else 'nothing (no channel configured or nothing new)'}")
    if args.check_links:
        st = check_experience_links(out_dir)
        print(f"Experience links: {sum(v == 'ok' for v in st.values())} ok, {sum(v == 'dead' for v in st.values())} dead, "
              f"{sum(v == 'unknown' for v in st.values())} unknown")

    bad = [r for r in report if not r["ok"]]
    print(f"Scanned {len(raw)} postings from {len(report) - len(bad)}/{len(report)} boards → "
          f"{len(rows)} internships ({result['counts']['jakarta']} Jakarta, {result['counts']['remote']} remote; "
          f"{result['counts']['cyber']} cyber, {result['counts']['tech']} tech, {result['counts']['new']} new)")
    for r in bad:
        print(f"  ! {r['company']} ({r['ats']}/{r['slug']}): {r['error']}")
    for r in rows[:args.top]:
        print(f"  {r['score']:>3}  {r['category']:<5} {r['where']:<9} {r['ghost_risk']:<6} {r['title']} — {r['company']}  {r['url']}")
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m jobsearch", description="Find Jakarta tech/cyber internships.")
    p.add_argument("--offline", action="store_true", help="use saved sample responses instead of the internet")
    p.add_argument("--companies", help="companies file (default: config/companies.json)")
    p.add_argument("--profile", default=str(ROOT / "config" / "profile.json"))
    p.add_argument("--out", default=str(ROOT / "data"), help="output folder (default: data/)")
    p.add_argument("--send-alert", action="store_true", help="send the daily alert via Telegram/email if configured")
    p.add_argument("--check-links", action="store_true", help="check the Experience tab links")
    p.add_argument("--top", type=int, default=20, help="how many results to print")
    args = p.parse_args(argv)
    run(args)
    return 0
