"""One module per hiring system (applicant tracking system, "ATS").

Each module exposes:
    fetch(company: dict, get_json) -> list[Job]
and optionally:
    details(job: Job, get_json) -> None   # fills job.text when the list API has no description
"""

from . import (amazon, ashby, email_alerts, greenhouse, jsonld, lever, recruitee, remote_boards, smartrecruiters,
               successfactors, teamtailor, workable, workday)

SOURCES = {
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
    "smartrecruiters": smartrecruiters,
    "workable": workable,
    "recruitee": recruitee,
    "teamtailor": teamtailor,
    "workday": workday,
    "successfactors": successfactors,
    "jsonld": jsonld,
    "remoteboard": remote_boards,
    "amazon": amazon,
    "email": email_alerts,
}

# Sources whose postings come straight from the employer's own hiring page.
COMPANY_SOURCES = {"greenhouse", "lever", "ashby", "smartrecruiters", "workable", "recruitee", "teamtailor",
                   "workday", "successfactors", "careerpage", "amazon"}

COUNTRY_NAMES = {"id": "Indonesia", "sg": "Singapore", "my": "Malaysia", "ph": "Philippines",
                 "th": "Thailand", "vn": "Vietnam", "au": "Australia"}
