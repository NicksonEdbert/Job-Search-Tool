"""Remember postings across daily runs: first seen, reposts and which ones closed."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import parse_iso

KEEP_DAYS = 180  # forget postings not seen for this long
CLOSED_WINDOW_DAYS = 45  # report postings that disappeared within this window as closed


def role_key(job) -> str:
    title = re.sub(r"[^a-z0-9]+", " ", (job.title or "").lower()).strip()
    return f"{job.company.lower()}|{title}"


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"roles": {}}


def save(path: Path, history: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=1, sort_keys=True), encoding="utf-8")


def update(history: dict, jobs: list, now: datetime = None, fetched_companies: set = None) -> list:
    """Update history in place and annotate jobs. Returns the list of closed postings.

    fetched_companies: companies whose boards loaded this run. Postings from a company whose
    board failed to load are NOT marked closed (we just couldn't see them).
    """
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat(timespec="seconds")
    roles = history.setdefault("roles", {})
    seen_keys = set()

    for job in jobs:
        key = role_key(job)
        seen_keys.add(key)
        entry = roles.get(key)
        if entry is None:
            entry = roles[key] = {"first_seen": stamp, "ids": [job.id], "reposts": 0,
                                  "company": job.company, "title": job.title}
            job.is_new = True
        else:
            if job.id not in entry["ids"]:
                # Same role, new posting id. Counts as a repost only if the old one went away.
                if entry.get("closed_at"):
                    entry["reposts"] = entry.get("reposts", 0) + 1
                entry["ids"].append(job.id)
                entry["ids"] = entry["ids"][-10:]
            job.is_new = bool(entry.get("closed_at"))  # back after closing: show it as new again
        entry.pop("closed_at", None)
        entry["last_seen"] = stamp
        entry["url"] = job.url
        job.first_seen = entry["first_seen"]
        job.reposts = entry.get("reposts", 0)

    closed = []
    for key, entry in list(roles.items()):
        last = parse_iso(entry.get("last_seen"))
        if last and now - last > timedelta(days=KEEP_DAYS):
            del roles[key]
            continue
        if key in seen_keys:
            continue
        if fetched_companies is not None and entry.get("company") not in fetched_companies:
            continue
        entry.setdefault("closed_at", stamp)
        closed_at = parse_iso(entry["closed_at"])
        if closed_at and now - closed_at <= timedelta(days=CLOSED_WINDOW_DAYS):
            closed.append({"ids": entry["ids"], "company": entry.get("company"), "title": entry.get("title"),
                           "closed_at": entry["closed_at"], "url": entry.get("url")})
    history["updated_at"] = stamp
    return closed


def open_days(history: dict, job, now: datetime = None):
    now = now or datetime.now(timezone.utc)
    first = parse_iso((history.get("roles", {}).get(role_key(job)) or {}).get("first_seen"))
    return None if first is None else (now - first).days
