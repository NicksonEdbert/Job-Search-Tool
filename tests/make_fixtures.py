"""Regenerate tests/fixtures/ (made-up sample responses in each hiring system's real format).

    python tests/make_fixtures.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from jobsearch.http import fixture_name  # noqa: E402
from jobsearch.sources import ashby, greenhouse, lever, smartrecruiters  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
HTTP = FIX / "http"


def ms(iso):
    return int(datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp() * 1000)


def put(url, data):
    HTTP.mkdir(parents=True, exist_ok=True)
    (HTTP / fixture_name(url)).write_text(json.dumps(data, indent=1), encoding="utf-8")


companies = [
    {"name": "Example Pay", "ats": "greenhouse", "slug": "examplepay"},
    {"name": "Example Logistics", "ats": "lever", "slug": "examplelogistics"},
    {"name": "Example Security", "ats": "ashby", "slug": "examplesec"},
    {"name": "Example Shop", "ats": "smartrecruiters", "slug": "exampleshop"},
    {"name": "Missing Co", "ats": "lever", "slug": "missingco"},
]

put(greenhouse.API.format(slug="examplepay"), {"jobs": [
    {"id": 101, "title": "Cyber Security Intern", "absolute_url": "https://job-boards.greenhouse.io/examplepay/jobs/101",
     "location": {"name": "Jakarta, Indonesia"}, "offices": [{"name": "Jakarta"}],
     "first_published": "2026-11-18T09:00:00-05:00", "updated_at": "2026-11-20T09:00:00-05:00",
     "content": "&lt;p&gt;A 3-month internship starting December 2026 in our security team.&lt;/p&gt;"
                "&lt;ul&gt;&lt;li&gt;Linux and Python basics&lt;/li&gt;&lt;li&gt;Wireshark, SIEM, OWASP Top 10&lt;/li&gt;"
                "&lt;li&gt;CTF experience is a plus&lt;/li&gt;&lt;/ul&gt;"},
    {"id": 102, "title": "Senior Backend Engineer", "absolute_url": "https://job-boards.greenhouse.io/examplepay/jobs/102",
     "location": {"name": "Jakarta"}, "offices": [], "first_published": "2026-11-10T00:00:00Z", "content": "5 years of experience"},
    {"id": 103, "title": "Software Engineer Intern", "absolute_url": "https://job-boards.greenhouse.io/examplepay/jobs/103",
     "location": {"name": "Singapore"}, "offices": [], "first_published": "2026-11-15T00:00:00Z", "content": ""},
    {"id": 104, "title": "Talent Pool - Internship (Technology)", "absolute_url": "https://job-boards.greenhouse.io/examplepay/jobs/104",
     "location": {"name": "Jakarta"}, "offices": [], "first_published": "2026-11-01T00:00:00Z",
     "content": "Send us your CV for future opportunities in software engineering."},
]})

put(lever.API.format(slug="examplelogistics"), [
    {"id": "aaa-1", "text": "Magang IT Support", "hostedUrl": "https://jobs.lever.co/examplelogistics/aaa-1",
     "categories": {"location": "Jakarta Selatan", "allLocations": ["Jakarta Selatan"]}, "country": "ID",
     "createdAt": ms("2026-11-20T03:00:00"),
     "descriptionPlain": "Program magang selama 6 bulan di tim IT.",
     "lists": [{"text": "Requirements", "content": "<li>Networking basics (TCP/IP)</li><li>Windows, Excel</li>"}],
     "additionalPlain": ""},
    {"id": "aaa-2", "text": "Marketing Intern", "hostedUrl": "https://jobs.lever.co/examplelogistics/aaa-2",
     "categories": {"location": "Jakarta"}, "country": "ID", "createdAt": ms("2026-11-19T03:00:00"),
     "descriptionPlain": "Help run social media campaigns.", "lists": []},
])

put(ashby.API.format(slug="examplesec"), {"jobs": [
    {"id": "s-1", "title": "SOC Analyst Intern", "location": "Jakarta, Indonesia", "secondaryLocations": [],
     "publishedAt": "2026-09-10T00:00:00.000+00:00", "isListed": True, "jobUrl": "https://jobs.ashbyhq.com/examplesec/s-1",
     "descriptionPlain": "Monitor alerts in our SIEM (Splunk) and help with incident response."},
    {"id": "s-2", "title": "Security Engineer Intern", "location": "Sydney", "secondaryLocations": [],
     "publishedAt": "2026-11-20T00:00:00.000+00:00", "isListed": True, "jobUrl": "https://jobs.ashbyhq.com/examplesec/s-2",
     "descriptionPlain": ""},
]})

sr_detail = "https://api.smartrecruiters.com/v1/companies/exampleshop/postings/9001"
put(smartrecruiters.API.format(slug="exampleshop", offset=0), {"totalFound": 2, "content": [
    {"id": "9001", "name": "Intern - Data Analytics", "releasedDate": "2026-11-21T02:00:00.000Z", "ref": sr_detail,
     "company": {"identifier": "ExampleShop"}, "location": {"city": "Jakarta", "country": "id", "fullLocation": "Jakarta, , Indonesia"}},
    {"id": "9002", "name": "Intern, Finance", "releasedDate": "2026-11-21T02:00:00.000Z",
     "ref": "https://api.smartrecruiters.com/v1/companies/exampleshop/postings/9002",
     "company": {"identifier": "ExampleShop"}, "location": {"city": "Bandung", "country": "id", "fullLocation": "Bandung, Indonesia"}},
]})
put(sr_detail, {"postingUrl": "https://jobs.smartrecruiters.com/ExampleShop/9001-intern-data-analytics", "active": True,
                "jobAd": {"sections": {
                    "jobDescription": {"title": "Job Description", "text": "<p>Internship from Jan - Mar 2027.</p>"},
                    "qualifications": {"title": "Qualifications", "text": "<ul><li>SQL, Python, Excel, Power BI</li>"
                                                                          "<li>Surat pengantar dari kampus</li></ul>"}}}})

(FIX / "companies.json").write_text(json.dumps({"companies": companies}, indent=1), encoding="utf-8")
print(f"wrote fixtures to {FIX}")
