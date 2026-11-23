"""Decide which postings are internships in Jakarta / Greater Jakarta, or remote roles open to Indonesia."""

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
REMOTE_RE = re.compile(r"\b(remote|anywhere|worldwide|work from home|wfh|telecommut\w*|distributed|fully remote)\b", re.I)
HYBRID_RE = re.compile(r"\bhybrid\b", re.I)

# Remote roles: who may apply?
OPEN_RE = re.compile(
    r"\b(worldwide|anywhere|global(ly)?|apac|asia|asia[- ]pacific|south ?east asia|sea region|indonesia|"
    r"gmt ?\+ ?[5-9]|utc ?\+ ?[5-9]|wib)\b",
    re.I,
)
ELSEWHERE_RE = re.compile(
    r"\b(us|usa|u\.s\.a?\.?|united states|north america|americas|canada|uk|united kingdom|britain|europe|eu|"
    r"emea|germany|deutschland|france|spain|italy|netherlands|poland|portugal|ireland|nordics|latam|"
    r"latin america|brazil|mexico|argentina|colombia|india|australia|new zealand|philippines|pakistan|"
    r"nigeria|kenya|africa|israel|japan|korea|singapore|malaysia|vietnam|thailand|hong kong|china|taiwan|"
    r"berlin|munich|münchen|hamburg|london|paris|amsterdam|new york|san francisco|toronto|"
    r"cet|est|pst|cst)\b",
    re.I,
)
ONLY_ELSEWHERE_TEXT_RE = re.compile(
    r"((must|need to|required to|should) (be )?(located|based|residing|reside|live|living) in (the )?"
    r"(us|usa|united states|canada|uk|united kingdom|europe|eu|germany|india|australia))|"
    r"(authori[sz]ed to work in (the )?(us|u\.s\.|united states|uk|united kingdom|eu|europe|canada|germany|australia))|"
    r"((us|u\.s\.) (citizens?|residents?|persons?) only)|"
    r"(only (open to|accepting|considering) (candidates|applicants|residents) (in|from|of) (the )?"
    r"(us|usa|united states|canada|uk|europe|eu|germany|india))",
    re.I,
)

# e.g. "Global Trainee Program 2027 (Hong Kong based)" listed under several cities
BASED_ELSEWHERE_RE = re.compile(
    r"\b(hong kong|singapore|bangkok|bkk|kuala lumpur|manila|taipei|shanghai|beijing|sydney|melbourne|"
    r"london|dubai|ho chi minh|hanoi|tokyo|seoul)[\s-]*based\b",
    re.I,
)


def is_internship(title: str) -> bool:
    return bool(INTERN_RE.search(title or ""))


def location_match(location: str, extra_places: tuple = ()) -> str:
    """'jakarta', 'indonesia' (country given, no city), 'remote', or '' (no match)."""
    loc = location or ""
    low = loc.lower()
    if JAKARTA_RE.search(loc) or any(p.lower() in low for p in extra_places):
        return "jakarta"
    if REMOTE_RE.search(loc):
        return "remote"
    if INDONESIA_RE.search(loc) and not OTHER_ID_CITY_RE.search(loc):
        return "indonesia"
    return ""


def work_mode(location: str, where: str) -> str:
    if where == "remote":
        return "remote"
    if HYBRID_RE.search(location or ""):
        return "hybrid"
    if REMOTE_RE.search(location or ""):
        return "remote"  # e.g. "Jakarta or Remote"
    return "onsite"


def remote_eligibility(job) -> tuple:
    """('open'|'unclear'|'blocked', reason) for someone working from Indonesia."""
    loc = job.location or ""
    text = (job.text or "")[:6000]
    # What's inside "Remote (...)" or after "Remote -"/"Remote,": that's where the board says applicants must be.
    if OPEN_RE.search(loc):
        return "open", ""
    region = REMOTE_RE.sub("", loc)
    m = ELSEWHERE_RE.search(region)
    if m:
        return "blocked", f"Remote, but only for {m.group(0)}"
    m = ONLY_ELSEWHERE_TEXT_RE.search(text)
    if m:
        return "blocked", f"Remote, but says: {m.group(0)}"
    if OPEN_RE.search(text):
        return "open", ""
    return "unclear", "Remote: check he can work from Indonesia"


def keep(job, extra_places: tuple = (), include_remote: bool = True) -> bool:
    if not is_internship(job.title) or BASED_ELSEWHERE_RE.search(job.title or ""):
        return False
    where = location_match(job.location, extra_places)
    if where == "remote":
        return include_remote and remote_eligibility(job)[0] != "blocked"
    return bool(where)
