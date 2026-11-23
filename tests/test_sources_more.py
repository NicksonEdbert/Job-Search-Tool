import argparse
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jobsearch import cli
from jobsearch.filter import keep, location_match, remote_eligibility, work_mode
from jobsearch.http import Client, FetchError, OfflineClient
from jobsearch.models import Job
from jobsearch.score import score
from jobsearch.sources import (amazon, email_alerts, jsonld, recruitee, remote_boards, successfactors, teamtailor,
                               workable, workday)

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parent.parent
C = OfflineClient()


def job(title, location, text="", source="remotive"):
    return Job(id=f"t:{title}", title=title, company="X", location=location, url="https://e.x", source=source, text=text)


class TestNewSources(unittest.TestCase):
    def test_workday(self):
        jobs = workday.fetch({"name": "Example Bank", "slug": "examplebank|wd3|Careers"}, C)
        titles = [j.title for j in jobs]
        self.assertEqual(titles, ["Cyber Security Intern", "Software Engineer Intern"])  # "Senior" dropped
        cyber = jobs[0]
        self.assertIn("Jakarta", cyber.location)          # from the detail page, not "2 Locations"
        self.assertIn("Hybrid", cyber.location)
        self.assertIn("SIEM", cyber.text)
        self.assertTrue(cyber.posted_at.startswith("2026-11-21"))
        self.assertEqual(jobs[1].location, "Singapore")    # not opened: not promising

    def test_workday_posted_text(self):
        self.assertTrue(workday.posted_from_text("Posted 3 Days Ago", NOW).startswith("2026-11-20"))
        self.assertTrue(workday.posted_from_text("Posted 30+ Days Ago", NOW).startswith("2026-10-23"))
        self.assertTrue(workday.posted_from_text("Posted Today", NOW).startswith("2026-11-23"))
        self.assertIsNone(workday.posted_from_text("", NOW))

    def test_successfactors(self):
        jobs = successfactors.fetch({"name": "Example Audit", "slug": "careers.example-audit.com"}, C)
        self.assertEqual([j.title for j in jobs], ["IT Risk & Cybersecurity Intern", "Audit Intern"])
        self.assertEqual(jobs[0].location, "Jakarta, ID")
        self.assertTrue(jobs[0].posted_at.startswith("2026-11-19"))
        self.assertIn("ISO 27001", jobs[0].text)
        self.assertNotIn("&amp;", jobs[0].url)

    def test_jsonld_and_robots(self):
        jobs = jsonld.fetch({"name": "Example Startup", "slug": "https://careers.example-startup.id/jobs"}, C)
        by_title = {j.title: j for j in jobs}
        self.assertEqual(set(by_title), {"Security Intern", "Data Intern"})
        self.assertEqual(by_title["Security Intern"].location, "Jakarta Selatan, ID")
        self.assertEqual(by_title["Data Intern"].location, "Remote (Indonesia)")
        # robots.txt disallows /jobs/private-*, so that page is never requested
        self.assertFalse(C.allowed("https://careers.example-startup.id/jobs/private-intern-789"))
        with self.assertRaises(FetchError):
            C.get_text("https://careers.example-startup.id/jobs/private-intern-789")

    def test_jsonld_parsing_variants(self):
        html = ('<script type="application/ld+json">{"@type": ["JobPosting"], "title": "A Intern",'
                ' "jobLocation": [{"address": {"addressLocality": "Jakarta"}}], "datePosted": "2026-11-01",}</script>')
        posts = jsonld.postings_in(html)  # trailing comma tolerated, list @type accepted
        self.assertEqual(len(posts), 1)
        self.assertEqual(jsonld.location_of(posts[0]), "Jakarta")

    def test_small_boards(self):
        wk = workable.fetch({"name": "Example Fin", "slug": "examplefin"}, C)
        self.assertEqual(wk[0].location, "Jakarta, DKI Jakarta, Indonesia")
        self.assertIn("Remote", wk[1].location)
        rc = recruitee.fetch({"name": "Example HR", "slug": "examplehr"}, C)
        self.assertIn("JavaScript", rc[0].text)
        tt = teamtailor.fetch({"name": "Example Hotel", "slug": "examplehotel"}, C)
        self.assertEqual((tt[0].title, tt[0].location), ("IT Support Intern", "Jakarta, Indonesia"))
        az = amazon.fetch({"name": "Amazon", "slug": "amazon"}, C)
        self.assertEqual([j.title for j in az], ["Cloud Support Associate Intern"])

    def test_remote_boards(self):
        rv = remote_boards.fetch({"name": "Remotive", "slug": "remotive"}, C)
        self.assertEqual(len(rv), 4)
        self.assertEqual(rv[0].company, "Global Sec")
        ok = remote_boards.fetch({"name": "RemoteOK", "slug": "remoteok"}, C)
        self.assertEqual(ok[0].location, "Remote (Asia)")


class TestRemoteRules(unittest.TestCase):
    def test_location_match(self):
        self.assertEqual(location_match("Jakarta; Remote"), "jakarta")
        self.assertEqual(location_match("Remote (Worldwide)"), "remote")
        self.assertEqual(location_match("Indonesia, Remote"), "remote")
        self.assertEqual(location_match("Indonesia"), "indonesia")
        self.assertEqual(work_mode("Jakarta, Hybrid", "jakarta"), "hybrid")
        self.assertEqual(work_mode("Jakarta", "jakarta"), "onsite")
        self.assertEqual(work_mode("Remote (APAC)", "remote"), "remote")

    def test_eligibility(self):
        self.assertEqual(remote_eligibility(job("Intern", "Remote (Worldwide)"))[0], "open")
        self.assertEqual(remote_eligibility(job("Intern", "Remote - APAC"))[0], "open")
        self.assertEqual(remote_eligibility(job("Intern", "Remote (USA Only)"))[0], "blocked")
        self.assertEqual(remote_eligibility(job("Intern", "Remote (Berlin)"))[0], "blocked")
        self.assertEqual(remote_eligibility(job("Intern", "Remote (Singapore)"))[0], "blocked")
        self.assertEqual(remote_eligibility(job("Intern", "Remote", "Must be authorized to work in the US."))[0], "blocked")
        self.assertEqual(remote_eligibility(job("Intern", "Remote", "We hire across Southeast Asia."))[0], "open")
        self.assertEqual(remote_eligibility(job("Intern", "Remote (location not stated)"))[0], "unclear")

    def test_keep_and_flag(self):
        self.assertTrue(keep(job("Security Intern", "Remote (Worldwide)")))
        self.assertFalse(keep(job("Security Intern", "Remote (USA Only)")))
        self.assertFalse(keep(job("Security Intern", "Remote (Worldwide)"), include_remote=False))
        vague = job("Data Intern", "Remote (location not stated)")
        score(vague, {}, now=NOW)
        self.assertEqual((vague.where, vague.work_mode), ("remote", "remote"))
        self.assertTrue(any("work from Indonesia" in f for f in vague.flags))

    def test_jakarta_beats_remote(self):
        a, b = job("Security Intern", "Jakarta"), job("Security Intern", "Remote (Worldwide)")
        score(a, {}, now=NOW)
        score(b, {}, now=NOW)
        self.assertGreater(a.score, b.score)


LINKEDIN_EMAIL = """<html><head><style>.x{color:red}</style></head><body><table>
<tr><td><a href="https://www.linkedin.com/comm/jobs/view/4012345678/?trackingId=abc&refId=xyz">Cyber Security Intern</a></td></tr>
<tr><td>Bank Example · Jakarta, Indonesia (Hybrid)</td></tr>
<tr><td><a href="https://www.linkedin.com/comm/jobs/view/4012345678/?trk=btn">View job</a></td></tr>
<tr><td><a href="https://www.linkedin.com/comm/jobs/view/4099999999/?trackingId=q">IT Intern</a></td></tr>
<tr><td>Startup Example</td></tr><tr><td>South Jakarta, Jakarta, Indonesia</td></tr>
<tr><td><a href="https://www.linkedin.com/comm/feed/">Home</a> Hi Student, unsubscribe</td></tr>
</table></body></html>"""
JOBSTREET_EMAIL = """<div><a href="https://id.jobstreet.com/id/job/81234567?ref=alert&cid=x"><b>Magang IT Security</b></a>
<p>PT Contoh Teknologi</p><p>Jakarta Selatan, Jakarta Raya</p>
<a href="https://id.jobstreet.com/id/job/81234567">Lihat lowongan</a></div>"""
GLINTS_EMAIL = """<a href="https://glints.com/id/opportunities/jobs/software-engineer-intern/6f1c2a3b-1111-2222-3333-444455556666?utm_source=email">
Software Engineer Intern</a><div>Contoh Startup</div><div>Jakarta Pusat, DKI Jakarta</div>"""


class FakeIMAP:
    def __init__(self, host):
        self.selected = None
        self.host = host

    def login(self, u, p):
        assert (u, p) == ("alerts@example.com", "abcdabcdabcdabcd")

    def select(self, box, readonly=False):
        assert readonly, "inbox must be opened read-only"
        self.selected = box
        return "OK", [b"2"]

    def search(self, charset, *criteria):
        return "OK", [b"1 2"]

    def fetch(self, mid, what):
        assert "PEEK" in what, "must not mark messages as read"
        html = LINKEDIN_EMAIL if mid == b"1" else JOBSTREET_EMAIL
        raw = (f"From: Job Alerts <jobalerts-noreply@linkedin.com>\r\nDate: Sat, 21 Nov 2026 01:00:00 +0000\r\n"
               f"Subject: New jobs\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{html}").encode()
        return "OK", [(b"1 (BODY[] {1})", raw)]

    def logout(self):
        pass


class TestEmailAlerts(unittest.TestCase):
    def test_linkedin(self):
        found = email_alerts.parse_html(LINKEDIN_EMAIL)
        self.assertEqual(len(found), 2)  # title link + "View job" link merged; Home link ignored
        a = next(f for f in found if f["id"] == "4012345678")
        self.assertEqual((a["title"], a["company"]), ("Cyber Security Intern", "Bank Example"))
        self.assertIn("Jakarta", a["location"])
        self.assertEqual(a["url"], "https://www.linkedin.com/jobs/view/4012345678/")  # tracking removed
        b = next(f for f in found if f["id"] == "4099999999")
        self.assertEqual((b["company"], b["location"]), ("Startup Example", "South Jakarta, Jakarta, Indonesia"))

    def test_jobstreet_and_glints(self):
        js = email_alerts.parse_html(JOBSTREET_EMAIL)[0]
        self.assertEqual((js["title"], js["company"], js["url"]),
                         ("Magang IT Security", "PT Contoh Teknologi", "https://id.jobstreet.com/job/81234567"))
        gl = email_alerts.parse_html(GLINTS_EMAIL)[0]
        self.assertEqual((gl["site"], gl["title"], gl["company"]), ("Glints", "Software Engineer Intern", "Contoh Startup"))
        self.assertNotIn("utm_source", gl["url"])

    def test_fetch_reads_inbox_read_only(self):
        env = {"ALERTS_IMAP_USER": "alerts@example.com", "ALERTS_IMAP_PASSWORD": "abcd abcd abcd abcd"}
        jobs = email_alerts.fetch({"name": "Job-alert emails", "slug": "imap.gmail.com"}, env=env, imap_cls=FakeIMAP)
        self.assertEqual({j.title for j in jobs}, {"Cyber Security Intern", "IT Intern", "Magang IT Security"})
        self.assertTrue(all(j.posted_at.startswith("2026-11-21") for j in jobs))
        self.assertTrue(all(j.source.endswith("-alert") for j in jobs))

    def test_not_configured(self):
        with self.assertRaises(email_alerts.NotConfigured):
            email_alerts.fetch({"name": "x"}, env={})


class TestPoliteClient(unittest.TestCase):
    def test_pacing_per_host(self):
        c = Client(delay=0.15)
        t0 = time.monotonic()
        for _ in range(3):
            c._pace("https://same.example.com/a")
        c._pace("https://other.example.com/a")  # different host: no wait
        self.assertGreaterEqual(time.monotonic() - t0, 0.29)
        self.assertLess(time.monotonic() - t0, 0.6)


class TestEndToEndAllSources(unittest.TestCase):
    def test_offline_run_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(offline=True, companies=None, profile=str(ROOT / "config" / "profile.json"),
                                      out=tmp, send_alert=False, check_links=False, top=0)
            res = cli.run(args, now=NOW)
            titles = {j["title"] for j in res["jobs"]}
            for t in ("Security Engineering Intern", "Cybersecurity Intern", "Data Analyst Intern",
                      "Cloud Support Associate Intern", "IT Support Intern", "QA Intern"):
                self.assertIn(t, titles)
            for t in ("Software Engineer Intern", "Frontend Intern", "IT Intern (Werkstudent)"):
                self.assertNotIn(t, titles)  # Singapore / US-only remote / Berlin-only remote
            self.assertGreaterEqual(res["counts"]["remote"], 3)
            failed = {s["company"]: s["error"] for s in res["sources"] if not s["ok"]}
            self.assertIn("not set up yet", failed["Job-alert emails"])
            remote = next(j for j in res["jobs"] if j["title"] == "Security Engineering Intern")
            self.assertEqual((remote["where"], remote["work_mode"]), ("remote", "remote"))


if __name__ == "__main__":
    unittest.main()
