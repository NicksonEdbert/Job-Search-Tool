"""Decide which postings to keep: work-experience roles (internships, entry-level/casual IT jobs, student jobs,
volunteer roles) in Jakarta or Melbourne, or remote roles open to someone in Indonesia/Australia."""

from __future__ import annotations

import re

INTERN_RE = re.compile(
    r"\b(intern|interns|internship|internships|magang|trainee|traineeship|pkl|apprentice|apprenticeship|"
    r"praktik kerja|kerja praktik|co-?op|vacationer|vacation program(me)?|work experience)\b|\bGIP\b|"
    r"\bgraduate (program|programme)\b|\bsummer (internship|program(me)?)\b",
    re.I,
)
VOLUNTEER_RE = re.compile(r"\b(volunteers?|volunteering|relawan)\b", re.I)
STUDENT_RE = re.compile(
    r"\b(student|casual academic|peer (mentor|leader|assisted)|pass leader|sessional tutor|tutor|"
    r"research assistant|ambassador)\b", re.I)
TEST_POSTING_RE = re.compile(r"\btest (job|posting|requisition|role|position)\b|\bmultiple test\b|\bdo not apply\b|"
                             r"\bdummy\b|\bplaceholder\b|\bwerkstudent\b", re.I)
ENTRY_RE = re.compile(
    r"\b(junior|jr\.?|graduate|grad|entry[- ]level|cadet|associate|level 1|l1|tier 1|t1|casual|part[- ]time)\b|"
    r"\b((it|technical|tech|desktop|deskside|end[- ]user|customer|application|computer) support)\b|"
    r"\b(service ?desk|help ?desk)\b|\bsupport (analyst|officer|technician|engineer|specialist|associate|consultant)\b|"
    r"\b(soc analyst|security operations analyst|it technician|field technician|it assistant|it officer)\b",
    re.I,
)
SENIOR_RE = re.compile(
    r"\b(senior|snr|sr\.?|lead|leader|principal|manager|head|director|staff|architect|vp|vice president|chief|"
    r"executive|expert|iii|iv)\b|\bteam lead", re.I)
YEARS_RE = re.compile(r"(\d+)\s*\+?\s*(?:-\s*\d+\s*)?(?:years?|yrs?|tahun)\s+(?:of\s+)?(?:\w+\s+){0,3}?(?:experience|pengalaman)",
                      re.I)
ROLE_TYPES = ("internship", "entry", "student", "volunteer")

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
# Greater Melbourne. Suburb names only count next to VIC/Victoria/Australia (Richmond etc. exist elsewhere).
MELBOURNE_RE = re.compile(r"\b(melbourne|docklands|southbank|cremorne|clayton)\b", re.I)
MELB_SUBURB_RE = re.compile(
    r"\b(richmond|collingwood|fitzroy|carlton|south yarra|st kilda|hawthorn|box hill|burwood|mulgrave|"
    r"notting hill|port melbourne|footscray|dandenong|camberwell|abbotsford|brunswick|cbd)\b", re.I)
VIC_RE = re.compile(r"\b(vic|victoria)\b.*\b(au|aus|australia)\b|\bvic\b|\b(victoria|melbourne),?\s*(au|aus|australia)\b", re.I)
REMOTE_RE = re.compile(r"\b(remote|anywhere|worldwide|work from home|wfh|telecommut\w*|distributed|fully remote)\b", re.I)
HYBRID_RE = re.compile(r"\bhybrid\b", re.I)

# Remote roles: who may apply?
OPEN_RE = re.compile(
    r"\b(worldwide|anywhere|global(ly)?|apac|asia|asia[- ]pacific|south ?east asia|sea region|indonesia|"
    r"australia|anz|oceania|gmt ?\+ ?([5-9]|1[01])|utc ?\+ ?([5-9]|1[01])|wib|aest|aedt)\b",
    re.I,
)
ELSEWHERE_RE = re.compile(
    r"\b(us|usa|u\.s\.a?\.?|united states|north america|americas|canada|uk|united kingdom|britain|europe|eu|"
    r"emea|germany|deutschland|france|spain|italy|netherlands|poland|portugal|ireland|nordics|latam|"
    r"latin america|brazil|mexico|argentina|colombia|india|philippines|pakistan|"
    r"nigeria|kenya|africa|israel|japan|korea|singapore|malaysia|vietnam|thailand|hong kong|china|taiwan|"
    r"berlin|munich|münchen|hamburg|london|paris|amsterdam|new york|san francisco|toronto|"
    r"cet|est|pst|cst)\b",
    re.I,
)
ONLY_ELSEWHERE_TEXT_RE = re.compile(
    r"((must|need to|required to|should) (be )?(located|based|residing|reside|live|living) in (the )?"
    r"(us|usa|united states|canada|uk|united kingdom|europe|eu|germany|india))|"
    r"(authori[sz]ed to work in (the )?(us|u\.s\.|united states|uk|united kingdom|eu|europe|canada|germany))|"
    r"((us|u\.s\.) (citizens?|residents?|persons?) only)|"
    r"(only (open to|accepting|considering) (candidates|applicants|residents) (in|from|of) (the )?"
    r"(us|usa|united states|canada|uk|europe|eu|germany|india))",
    re.I,
)

# e.g. "Global Trainee Program 2027 (Hong Kong based)" listed under several cities
BASED_ELSEWHERE_RE = re.compile(
    r"\b(hong kong|singapore|bangkok|bkk|kuala lumpur|manila|taipei|shanghai|beijing|sydney|brisbane|perth|"
    r"london|dubai|ho chi minh|hanoi|tokyo|seoul)[\s-]*based\b",
    re.I,
)


# Australian roles he can't take on a student visa (hidden), or should double-check (flagged).
AU_BLOCK_RE = re.compile(
    r"(must (be|hold) (an )?australian citizen(ship)?)|(australian citizen(ship)? (is )?(only|required|essential))|"
    r"(australian citizens?( (and|or) (australian )?permanent residents?)? only)|"
    r"(open (only )?to australian (citizens|and new zealand citizens))|(citizens? (or|and) permanent residents? (of australia )?only)|"
    r"(must (be|hold) (an? )?(australian )?(citizen|permanent resident))|(permanent residen(t|cy) (is )?required)|"
    r"\b(nv1|nv2|negative vetting|agsva)\b|(baseline (security )?clearance)|(security clearance (is )?(required|essential|mandatory))|"
    r"(ability to (obtain|gain|hold)( and maintain)? (an? )?(australian government )?(security )?clearance)",
    re.I,
)
AU_FLAG_RE = re.compile(r"(full|unrestricted|unlimited) (working|work) rights", re.I)


def is_internship(title: str) -> bool:
    return bool(INTERN_RE.search(title or ""))


def role_type(title: str):
    """'internship' | 'volunteer' | 'student' | 'entry' | None (not a work-experience role)."""
    t = title or ""
    if INTERN_RE.search(t):
        return "internship"
    if VOLUNTEER_RE.search(t):
        return "volunteer"
    if SENIOR_RE.search(t):
        return None
    if STUDENT_RE.search(t):
        return "student"
    if ENTRY_RE.search(t):
        return "entry"
    return None


def relevant_title(title: str) -> bool:
    """Cheap pre-filter for readers that must decide which postings to open."""
    return role_type(title) is not None


def max_years(text: str) -> int:
    ys = [int(m.group(1)) for m in YEARS_RE.finditer(text or "") if int(m.group(1)) <= 15]
    return max(ys) if ys else 0


def is_australian(job) -> bool:
    return bool(MELBOURNE_RE.search(job.location or "") or VIC_RE.search(job.location or "")
                or re.search(r"\baustralia\b", job.location or "", re.I))


def au_work_rights(job) -> tuple:
    """('blocked'|'flag'|'ok', reason) for an international student in Australia."""
    text = f"{job.title}\n{(job.text or '')[:8000]}"
    m = AU_BLOCK_RE.search(text)
    if m:
        return "blocked", f"Needs {m.group(0).strip()}"
    if AU_FLAG_RE.search(text):
        return "flag", "Asks for full working rights: on a student visa he has unlimited hours only during breaks"
    return "ok", ""


def location_match(location: str, extra_places: tuple = (), cities: tuple = ("jakarta", "melbourne")) -> str:
    """'jakarta', 'melbourne', 'indonesia' (country given, no city), 'remote', or '' (no match)."""
    loc = location or ""
    low = loc.lower()
    if "jakarta" in cities and (JAKARTA_RE.search(loc) or any(p.lower() in low for p in extra_places)):
        return "jakarta"
    if "melbourne" in cities and (MELBOURNE_RE.search(loc) or VIC_RE.search(loc)
                                  or (MELB_SUBURB_RE.search(loc) and re.search(r"\b(vic|victoria|australia)\b", loc, re.I))):
        return "melbourne"
    if REMOTE_RE.search(loc):
        return "remote"
    if "jakarta" in cities and INDONESIA_RE.search(loc) and not OTHER_ID_CITY_RE.search(loc):
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
    return "unclear", "Remote: check he can work from Indonesia or Australia"


def keep(job, extra_places: tuple = (), include_remote: bool = True, cities: tuple = ("jakarta", "melbourne"),
         role_types: tuple = ROLE_TYPES) -> bool:
    kind = role_type(job.title)
    if TEST_POSTING_RE.search(job.title or ""):
        return False  # recruiters' test postings; German student jobs that need German enrolment
    if kind is None or kind not in role_types or BASED_ELSEWHERE_RE.search(job.title or ""):
        return False
    if kind in ("entry", "student") and max_years(job.text) >= 3:
        return False  # "junior" in name only
    where = location_match(job.location, extra_places, cities)
    if not where:
        return False
    if where == "remote" and not (include_remote and remote_eligibility(job)[0] != "blocked"):
        return False
    if (where == "melbourne" or is_australian(job)) and au_work_rights(job)[0] == "blocked":
        return False
    return True
