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


def put(url, data, body=None):
    HTTP.mkdir(parents=True, exist_ok=True)
    (HTTP / fixture_name(url, body)).write_text(json.dumps(data, indent=1), encoding="utf-8")


def put_text(url, text):
    HTTP.mkdir(parents=True, exist_ok=True)
    (HTTP / fixture_name(url, ext=".txt")).write_text(text, encoding="utf-8")


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

# ---- Workday ------------------------------------------------------------------------------------
wd_api = "https://examplebank.wd3.myworkdayjobs.com/wday/cxs/examplebank/Careers"
put(f"{wd_api}/jobs", {"total": 3, "jobPostings": [
    {"title": "Cyber Security Intern", "externalPath": "/job/Jakarta/Cyber-Security-Intern_R100",
     "locationsText": "2 Locations", "postedOn": "Posted 2 Days Ago"},
    {"title": "Software Engineer Intern", "externalPath": "/job/Singapore/Software-Engineer-Intern_R101",
     "locationsText": "Singapore", "postedOn": "Posted Today"},
    {"title": "Senior Risk Analyst", "externalPath": "/job/Jakarta/Senior-Risk-Analyst_R102",
     "locationsText": "Jakarta", "postedOn": "Posted 30+ Days Ago"},
]}, body={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "intern Indonesia"})
put(f"{wd_api}/job/Jakarta/Cyber-Security-Intern_R100", {"jobPostingInfo": {
    "title": "Cyber Security Intern", "location": "Jakarta", "additionalLocations": ["Singapore"],
    "startDate": "2026-11-21", "remoteType": "Hybrid",
    "jobDescription": "<p>3-month internship from December 2026 in our SOC.</p><ul><li>Python, Linux, SIEM</li></ul>",
    "externalUrl": "https://examplebank.wd3.myworkdayjobs.com/Careers/job/Jakarta/Cyber-Security-Intern_R100"}})

# ---- SuccessFactors -----------------------------------------------------------------------------
sf = "careers.example-audit.com"
put_text(f"https://{sf}/robots.txt", "User-agent: *\nDisallow: /private/\n")
put_text(f"https://{sf}/search/?q=intern&locationsearch=Indonesia&sortColumn=referencedate&sortDirection=desc&startrow=0", """
<table id="searchresults"><tbody>
<tr class="data-row"><td class="colTitle"><span class="jobTitle hidden-phone">
  <a href="/job/Jakarta-IT-Risk-&amp;-Cybersecurity-Intern-ID/1111/" class="jobTitle-link">IT Risk &amp; Cybersecurity Intern</a></span></td>
  <td class="colLocation"><span class="jobLocation">Jakarta, ID</span></td><td class="colDate"><span class="jobDate">Nov 19, 2026</span></td></tr>
<tr class="data-row"><td class="colTitle"><span class="jobTitle hidden-phone">
  <a href="/job/Jakarta-Audit-Intern-ID/2222/" class="jobTitle-link">Audit Intern</a></span></td>
  <td class="colLocation"><span class="jobLocation">Jakarta, ID</span></td><td class="colDate"><span class="jobDate">Oct 1, 2026</span></td></tr>
<tr class="data-row"><td class="colTitle"><span class="jobTitle hidden-phone">
  <a href="/job/Jakarta-Tax-Manager-ID/3333/" class="jobTitle-link">Tax Manager</a></span></td>
  <td class="colLocation"><span class="jobLocation">Jakarta, ID</span></td><td class="colDate"><span class="jobDate">Nov 20, 2026</span></td></tr>
</tbody></table>""")
put_text(f"https://{sf}/job/Jakarta-IT-Risk-&amp;-Cybersecurity-Intern-ID/1111/".replace("&amp;", "&"),
         '<html><span class="jobdescription"><div><p>Join our cyber team for 3 months. Skills: ISO 27001, '
         'vulnerability assessment, Python.</p></div></span></html>')
put_text(f"https://{sf}/job/Jakarta-Audit-Intern-ID/2222/",
         '<html><span class="jobdescription"><div><p>Financial audit internship, 6 months.</p></div></span></html>')

# ---- Generic career page with JSON-LD -----------------------------------------------------------
cp = "https://careers.example-startup.id"
put_text(f"{cp}/robots.txt", "User-agent: *\nDisallow: /jobs/private-\n")
put_text(f"{cp}/jobs", f"""<html><body>
<a href="/jobs/security-intern-123">Security Intern</a>
<a href="/jobs/data-intern-remote-456">Data Intern (Remote)</a>
<a href="/jobs/private-intern-789">Hidden intern page (robots says no)</a>
<a href="/jobs/marketing-manager-9">Marketing Manager</a>
<a href="/about">About</a></body></html>""")
put_text(f"{cp}/jobs/security-intern-123", """<html><head><script type="application/ld+json">
{"@context": "https://schema.org", "@type": "JobPosting", "title": "Security Intern", "identifier": {"value": "123"},
 "datePosted": "2026-11-20", "description": "<p>Pentest and OWASP basics. Start immediately.</p>",
 "hiringOrganization": {"@type": "Organization", "name": "Example Startup"},
 "jobLocation": {"@type": "Place", "address": {"addressLocality": "Jakarta Selatan", "addressCountry": "ID"}}}
</script></head><body>Security Intern</body></html>""")
put_text(f"{cp}/jobs/data-intern-remote-456", """<html><head><script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [{"@type": "WebPage"}, {"@type": "JobPosting", "title": "Data Intern",
 "identifier": "456", "datePosted": "2026-11-15", "description": "SQL and Python.", "jobLocationType": "TELECOMMUTE",
 "applicantLocationRequirements": {"@type": "Country", "name": "Indonesia"},
 "hiringOrganization": {"name": "Example Startup"}}]}
</script></head></html>""")

# ---- Workable / Recruitee / Teamtailor ----------------------------------------------------------
put("https://apply.workable.com/api/v1/widget/accounts/examplefin?details=true", {"name": "Example Fin", "jobs": [
    {"title": "IT Security Intern", "shortcode": "AB12", "url": "https://apply.workable.com/j/AB12",
     "published_on": "2026-11-18", "city": "Jakarta", "country": "Indonesia", "telecommuting": False,
     "locations": [{"city": "Jakarta", "region": "DKI Jakarta", "country": "Indonesia", "hidden": False}],
     "description": "<p>Help our security team with access reviews and phishing tests.</p>"},
    {"title": "Product Intern", "shortcode": "CD34", "url": "https://apply.workable.com/j/CD34",
     "published_on": "2026-11-10", "country": "Indonesia", "telecommuting": True, "locations": []},
]})
put("https://examplehr.recruitee.com/api/offers/", {"offers": [
    {"id": 77, "title": "QA Intern", "status": "published", "city": "Jakarta", "country": "Indonesia", "remote": False,
     "careers_url": "https://examplehr.recruitee.com/o/qa-intern", "published_at": "2026-11-19 08:00:00 UTC",
     "description": "<p>Manual and automated testing.</p>", "requirements": "<p>Basic JavaScript.</p>"}]})
put_text("https://examplehotel.teamtailor.com/jobs.rss", """<?xml version="1.0"?>
<rss version="2.0" xmlns:tt="https://teamtailor.com/locations"><channel><title>Jobs</title>
<item><title>IT Support Intern</title><link>https://examplehotel.teamtailor.com/jobs/55-it-support-intern</link>
<guid>55</guid><pubDate>Fri, 20 Nov 2026 03:00:00 +0000</pubDate><description>&lt;p&gt;Help desk and networking.&lt;/p&gt;</description>
<tt:locations><tt:location><tt:city>Jakarta</tt:city><tt:country>Indonesia</tt:country></tt:location></tt:locations>
</item></channel></rss>""")

# ---- Amazon -------------------------------------------------------------------------------------
put("https://www.amazon.jobs/en/search.json?base_query=intern&loc_query=Indonesia&result_limit=100&sort=recent", {"jobs": [
    {"id_icims": "300001", "title": "Cloud Support Associate Intern", "company_name": "Amazon Web Services Indonesia",
     "normalized_location": "Jakarta, Jakarta, IDN", "location": "ID, JK, Jakarta", "posted_date": "November 17, 2026",
     "job_path": "/en/jobs/300001/cloud-support-associate-intern", "description": "Linux, networking, AWS."},
    {"id_icims": "300002", "title": "Software Development Engineer", "company_name": "Amazon",
     "normalized_location": "Jakarta, IDN", "posted_date": "November 17, 2026", "job_path": "/en/jobs/300002/sde"}]})

# ---- Remote job boards --------------------------------------------------------------------------
put("https://remotive.com/api/remote-jobs?search=intern", {"jobs": [
    {"id": 9001, "title": "Security Engineering Intern", "company_name": "Global Sec", "candidate_required_location": "Worldwide",
     "publication_date": "2026-11-20T10:00:00", "url": "https://remotive.com/remote-jobs/9001", "description": "<p>Threat detection.</p>"},
    {"id": 9002, "title": "Software Engineer Intern", "company_name": "US Startup", "candidate_required_location": "USA Only",
     "publication_date": "2026-11-20T10:00:00", "url": "https://remotive.com/remote-jobs/9002", "description": ""},
    {"id": 9003, "title": "Data Analyst Intern", "company_name": "Vague Co", "candidate_required_location": "",
     "publication_date": "2026-11-19T10:00:00", "url": "https://remotive.com/remote-jobs/9003", "description": "<p>SQL.</p>"},
    {"id": 9004, "title": "Frontend Intern", "company_name": "Strict Co", "candidate_required_location": "",
     "publication_date": "2026-11-19T10:00:00", "url": "https://remotive.com/remote-jobs/9004",
     "description": "<p>You must be authorized to work in the United States.</p>"}]})
put("https://remotive.com/api/remote-jobs?search=internship", {"jobs": []})
put("https://remotive.com/api/remote-jobs?search=trainee", {"jobs": []})
put("https://www.arbeitnow.com/api/job-board-api", {"data": [
    {"slug": "werkstudent-intern-berlin", "title": "IT Intern (Werkstudent)", "company_name": "Berlin GmbH", "remote": True,
     "location": "Berlin", "created_at": 1795600000, "url": "https://www.arbeitnow.com/jobs/x", "description": "", "job_types": []}],
    "links": {"next": None}})
put("https://remoteok.com/api", [{"legal": "attribution required"},
    {"id": "77", "position": "Cybersecurity Intern", "company": "APAC Shield", "location": "Asia",
     "date": "2026-11-21T00:00:00+00:00", "url": "https://remoteok.com/remote-jobs/77", "description": "SOC work"}])

companies += [
    {"name": "Example Bank", "ats": "workday", "slug": "examplebank|wd3|Careers"},
    {"name": "Example Audit", "ats": "successfactors", "slug": sf},
    {"name": "Example Startup", "ats": "jsonld", "slug": f"{cp}/jobs"},
    {"name": "Example Fin", "ats": "workable", "slug": "examplefin"},
    {"name": "Example HR", "ats": "recruitee", "slug": "examplehr"},
    {"name": "Example Hotel", "ats": "teamtailor", "slug": "examplehotel"},
    {"name": "Amazon", "ats": "amazon", "slug": "amazon"},
    {"name": "Remotive", "ats": "remoteboard", "slug": "remotive"},
    {"name": "Arbeitnow", "ats": "remoteboard", "slug": "arbeitnow"},
    {"name": "RemoteOK", "ats": "remoteboard", "slug": "remoteok"},
    {"name": "Job-alert emails", "ats": "email", "slug": "imap.gmail.com"},
]

(FIX / "companies.json").write_text(json.dumps({"companies": companies}, indent=1), encoding="utf-8")
print(f"wrote fixtures to {FIX}")
