"""Estimate how likely a posting is a 'ghost' (not really hiring). A guess, not a verdict."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import parse_iso

EVERGREEN_RE = re.compile(
    r"talent (pool|community|network)|general application|future (opportunit|opening|role)|"
    r"always hiring|evergreen|open application|expression of interest|pipeline role|"
    r"kirim(kan)? cv (anda )?untuk (posisi|kebutuhan) (mendatang|masa depan)",
    re.I,
)
COMPANY_BOARDS = {"greenhouse", "lever", "ashby", "smartrecruiters", "workable"}


def assess(job, now: datetime = None, open_days: int = None) -> None:
    """Fill job.ghost_risk ('low'|'medium'|'high') and job.ghost_reasons.

    open_days: how long our history has seen this posting open (None if unknown).
    """
    now = now or datetime.now(timezone.utc)
    points = 0
    reasons = []

    posted = parse_iso(job.posted_at)
    if posted:
        age = (now - posted).days
        if age > 60:
            points += 3
            reasons.append(f"Posted {age} days ago")
        elif age > 30:
            points += 2
            reasons.append(f"Posted {age} days ago")
    if open_days is not None and open_days > 60 and not (posted and (now - posted).days > 60):
        points += 2
        reasons.append(f"Open for {open_days} days")

    if job.reposts >= 2:
        points += 3
        reasons.append(f"Reposted {job.reposts} times")
    elif job.reposts == 1:
        points += 2
        reasons.append("Taken down and reposted")

    if EVERGREEN_RE.search(job.title or ""):
        points += 3
        reasons.append("Title says talent pool / future openings: likely collecting CVs")
    elif EVERGREEN_RE.search((job.text or "")[:1500]):
        points += 2
        reasons.append("Mentions a talent pool: may collect CVs rather than fill one role")

    if job.source not in COMPANY_BOARDS:
        points += 1
        reasons.append("Not from the company's own hiring page")

    if any("inactive" in f.lower() for f in job.flags):
        points += 3
        reasons.append("Company marked the posting inactive")

    job.ghost_risk = "high" if points >= 3 else "medium" if points >= 2 else "low"
    if job.ghost_risk == "low":
        reasons.append("Fresh posting on the company's own hiring page" if job.source in COMPANY_BOARDS
                       else "No warning signs found")
    job.ghost_reasons = reasons
