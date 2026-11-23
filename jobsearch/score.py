"""Rank internships: cybersecurity first, other tech next, then timing, freshness and ghost risk."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from .filter import location_match
from .models import parse_iso

CYBER_TITLE = [
    r"security", r"cyber", r"infosec", r"\bsoc\b", r"pen ?test", r"penetration", r"red team", r"blue team",
    r"threat", r"incident response", r"\bgrc\b", r"it audit", r"it risk", r"technology risk", r"vulnerab",
    r"\bdfir\b", r"forensic", r"appsec", r"devsecops", r"keamanan", r"fraud (analyst|detection|risk)",
    r"identity and access", r"\biam\b",
]
# Stronger phrases only, because "security" alone appears in a lot of boilerplate.
CYBER_TEXT = [
    r"cyber ?security", r"information security", r"infosec", r"penetration test", r"\bsoc analyst",
    r"security operations", r"incident response", r"vulnerability (assessment|management|scan)",
    r"threat (intelligence|hunting|detection)", r"\bsiem\b", r"\bowasp\b", r"iso ?27001", r"red team",
    r"blue team", r"\bctf\b", r"security engineer", r"security analyst", r"keamanan (siber|informasi)",
]
TECH_TITLE = [
    r"software", r"engineer", r"developer", r"\bdev\b", r"back-?end", r"front-?end", r"full-?stack",
    r"mobile", r"android", r"\bios\b", r"\bweb\b", r"\bdata\b", r"machine learning", r"\bml\b", r"\bai\b",
    r"\bqa\b", r"quality assurance", r"\btest", r"devops", r"\bsre\b", r"cloud", r"infrastructure",
    r"network", r"\bit\b", r"sysadmin", r"system", r"tech", r"product (management|manager|design)",
    r"analytics", r"programmer", r"automation",
]
TECH_TEXT = [r"python", r"javascript", r"java\b", r"\bsql\b", r"linux", r"software development", r"programming"]

MONTHS_RE = re.compile(r"(\d{1,2})\s*(?:-|–|to|sampai|hingga)?\s*(\d{1,2})?\s*(months?|bulan)", re.I)
START_NOW_RE = re.compile(
    r"\b(immediate(ly)?|asap|as soon as possible|segera|start(ing)? (in |from )?(dec(ember)?|jan(uary)?)|"
    r"desember|januari|dec(ember)? 2026|jan(uary)? 2027)\b",
    re.I,
)
LATER_RE = re.compile(r"\b(summer (internship )?2027|(jun|june|jul|july|aug|august) 2027|2028)\b", re.I)
LETTER_RE = re.compile(
    r"surat (pengantar|rekomendasi|keterangan)|(university|campus|kampus) (letter|recommendation)|"
    r"kampus merdeka|\bmsib\b|internship credit|academic credit|wajib magang", re.I,
)
EXPERIENCE_RE = re.compile(r"(\d+)\s*\+?\s*(?:years?|tahun)\s+(?:of\s+)?(?:work(?:ing)?\s+|relevant\s+|professional\s+)?(?:experience|pengalaman)", re.I)
FINAL_YEAR_RE = re.compile(r"\b(final[- ]year|fresh graduate|recent graduate|graduated|lulusan)\b", re.I)


_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_MONTHS.update({"mei": 5, "agu": 8, "okt": 10, "des": 12})  # Bahasa Indonesia spellings
_MON = r"(jan|feb|mar|apr|may|mei|jun|jul|aug|agu|sep|oct|okt|nov|dec|des)[a-z]*\.?"
RANGE_RE = re.compile(_MON + r"\s*(20\d\d)?\s*(?:-|–|—|to|until|sampai|hingga|s/d)\s*" + _MON + r"\s*(20\d\d)?", re.I)


def month_ranges(text: str) -> list:
    """[(start_month, start_year|None, months_long)] for phrases like 'Jan - June 2027'."""
    out = []
    for m in RANGE_RE.finditer(text):
        a, ya, b, yb = m.group(1).lower()[:3], m.group(2), m.group(3).lower()[:3], m.group(4)
        ma, mb = _MONTHS[a], _MONTHS[b]
        length = (mb - ma) % 12 + 1
        year = int(ya) if ya else (int(yb) - (1 if mb < ma else 0) if yb else None)
        out.append((ma, year, length))
    return out


def _any(patterns, text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def categorize(job, profile: dict) -> str:
    title = job.title or ""
    text = job.text or ""
    cyber_title = CYBER_TITLE + [re.escape(k) for k in profile.get("cyber_keywords", [])]
    tech_title = TECH_TITLE + [re.escape(k) for k in profile.get("tech_keywords", [])]
    if _any(cyber_title, title) or (_any(CYBER_TEXT, text) and _any(tech_title, title)):
        return "cyber"
    if _any(tech_title, title) or _any(CYBER_TEXT, text):
        return "tech"
    if _any(TECH_TEXT, text) and re.search(r"\b(engineering|technology|it)\b", title + " " + text[:400], re.I):
        return "tech"
    return "other"


def timing(job, profile: dict) -> tuple:
    """Return (timing label, flags) for someone available now for a short stint."""
    text = f"{job.title}\n{job.text}"
    max_months = int(profile.get("max_months", 3))
    flags = []
    label = "unknown"
    months = []
    for m in MONTHS_RE.finditer(text):
        nums = [int(x) for x in (m.group(1), m.group(2)) if x]
        if nums and max(nums) <= 24:
            months.append(max(nums))
    later_start = None
    for start, year, length in month_ranges(text):
        months.append(length)
        # He's free Dec-Feb; a programme starting Mar 2027 or later is "later".
        if year and (year, start) >= (2027, 3) and (year, start) <= (2028, 6):
            later_start = f"{list(_MONTHS)[start - 1].title()} {year}"
        elif start in (11, 12, 1, 2):
            label = "good"
    if START_NOW_RE.search(text):
        label = "good"
    if months:
        longest = max(months)
        if longest >= 6:
            label = "long"
            flags.append(f"Asks for {longest} months; he's free about {max_months}")
        elif longest > max_months and label != "good":
            label = "check"
            flags.append(f"{longest}-month internship; check if a shorter stint is OK")
        elif label == "unknown":
            label = "good"
    if later_start and label != "long":
        label = "later"
        flags.append(f"Starts {later_start}")
    elif LATER_RE.search(job.title or "") and label not in ("long",):
        label = "later"
        flags.append("Starts later (2027 programme)")
    if LETTER_RE.search(text):
        flags.append("May need a letter from his university")
    exp = [int(m.group(1)) for m in EXPERIENCE_RE.finditer(text) if int(m.group(1)) <= 15]
    if exp and max(exp) >= 1:
        flags.append(f"Asks for {max(exp)}+ years of experience")
    if FINAL_YEAR_RE.search(text):
        flags.append("Mentions final-year students or graduates; check eligibility")
    return label, flags


def days_since(iso: str, now: datetime):
    dt = parse_iso(iso)
    return None if dt is None else max(0, (now - dt).days)


def score(job, profile: dict, now: datetime = None) -> None:
    """Fill job.category, job.timing, job.flags and job.score (0-100)."""
    now = now or datetime.now(timezone.utc)
    job.category = categorize(job, profile)
    job.timing, timing_flags = timing(job, profile)
    job.flags = list(dict.fromkeys(job.flags + timing_flags))

    s = {"cyber": 50, "tech": 30, "other": 0}[job.category]
    s += 10 if location_match(job.location, tuple(profile.get("extra_places", []))) == "jakarta" else 5
    s += {"good": 12, "unknown": 4, "check": 0, "later": -10, "long": -15}[job.timing]
    age = days_since(job.posted_at or job.first_seen, now)
    if age is not None:
        s += 15 if age <= 7 else 10 if age <= 14 else 5 if age <= 30 else 0
    if any("years of experience" in f for f in job.flags):
        s -= 10
    s -= {"low": 0, "medium": 8, "high": 20}.get(job.ghost_risk, 0)
    job.score = max(0, min(100, s))
