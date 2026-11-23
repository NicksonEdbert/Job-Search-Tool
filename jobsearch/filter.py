"""Decide which postings are internships in Jakarta / Greater Jakarta."""

from __future__ import annotations

import re

INTERN_RE = re.compile(
    r"\b(intern|interns|internship|internships|magang|trainee|traineeship|pkl|apprentice|apprenticeship|"
    r"praktik kerja|kerja praktik|co-?op)\b|\bGIP\b|\bgraduate (program|programme)\b",
    re.I,
)

# Jakarta, Greater Jakarta (Jabodetabek) and common Jakarta districts/business areas.
JAKARTA_RE = re.compile(
    r"\b(jakarta|jkt|dki|jabodetabek|tangerang|bsd|serpong|bekasi|depok|bogor|"
    r"setiabudi|setia budi|kuningan|sudirman|thamrin|scbd|kebayoran|menteng|tanah abang|gambir|senayan|"
    r"kemang|pluit|kelapa gading|cilandak|pancoran|mampang|tebet|kemayoran|pondok indah|"
    r"kebon jeruk|cengkareng|grogol|tomang|slipi|semanggi|gatot subroto|tb simatupang)\b",
    re.I,
)
INDONESIA_RE = re.compile(r"\bindonesia\b", re.I)
OTHER_ID_CITY_RE = re.compile(
    r"\b(surabaya|bandung|medan|bali|denpasar|yogyakarta|jogja|semarang|makassar|batam|malang|palembang|balikpapan)\b",
    re.I,
)


def is_internship(title: str) -> bool:
    return bool(INTERN_RE.search(title or ""))


def location_match(location: str, extra_places: tuple = ()) -> str:
    """'jakarta', 'indonesia' (country given, no city) or '' (no match)."""
    loc = location or ""
    low = loc.lower()
    if JAKARTA_RE.search(loc) or any(p.lower() in low for p in extra_places):
        return "jakarta"
    if INDONESIA_RE.search(loc) and not OTHER_ID_CITY_RE.search(loc):
        return "indonesia"
    return ""


# e.g. "Global Trainee Program 2027 (Hong Kong based)" listed under several cities
BASED_ELSEWHERE_RE = re.compile(
    r"\b(hong kong|singapore|bangkok|bkk|kuala lumpur|manila|taipei|shanghai|beijing|sydney|melbourne|"
    r"london|dubai|ho chi minh|hanoi|tokyo|seoul)[\s-]*based\b",
    re.I,
)


def keep(job, extra_places: tuple = ()) -> bool:
    if not is_internship(job.title) or BASED_ELSEWHERE_RE.search(job.title or ""):
        return False
    return bool(location_match(job.location, extra_places))
