"""One module per hiring system (applicant tracking system, "ATS").

Each module exposes:
    fetch(company: dict, get_json) -> list[Job]
and optionally:
    details(job: Job, get_json) -> None   # fills job.text when the list API has no description
"""

from . import ashby, greenhouse, lever, smartrecruiters

SOURCES = {
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
    "smartrecruiters": smartrecruiters,
}

COUNTRY_NAMES = {"id": "Indonesia", "sg": "Singapore", "my": "Malaysia", "ph": "Philippines",
                 "th": "Thailand", "vn": "Vietnam", "au": "Australia"}
