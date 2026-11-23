import argparse
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jobsearch import cli, digest, ghost, history
from jobsearch.filter import is_internship, keep, location_match
from jobsearch.http import offline_get_json
from jobsearch.models import Job, html_to_text, to_iso
from jobsearch.score import month_ranges, score
from jobsearch.sources import ashby, greenhouse, lever, smartrecruiters

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parent.parent
GET = offline_get_json()


def job(title="Software Engineer Intern", location="Jakarta", text="", posted_days=3, source="greenhouse", **kw):
    return Job(id=kw.pop("id", f"x:{title}"), title=title, company=kw.pop("company", "Acme"), location=location,
               url="https://example.com", source=source,
               posted_at=to_iso((NOW - timedelta(days=posted_days)).isoformat()) if posted_days is not None else None,
               text=text, **kw)


class TestSources(unittest.TestCase):
    def test_greenhouse(self):
        jobs = greenhouse.fetch({"name": "Example Pay", "slug": "examplepay"}, GET)
        self.assertEqual(len(jobs), 4)
        j = jobs[0]
        self.assertEqual(j.id, "greenhouse:examplepay:101")
        self.assertIn("Jakarta", j.location)
        self.assertIn("Wireshark", j.text)  # double-escaped HTML decoded
        self.assertNotIn("<li>", j.text)
        self.assertTrue(j.posted_at.startswith("2026-11-18T14:00"))

    def test_lever(self):
        jobs = lever.fetch({"name": "Example Logistics", "slug": "examplelogistics"}, GET)
        self.assertEqual(jobs[0].title, "Magang IT Support")
        self.assertIn("TCP/IP", jobs[0].text)
        self.assertTrue(jobs[0].posted_at.startswith("2026-11-20"))

    def test_ashby(self):
        jobs = ashby.fetch({"name": "Example Security", "slug": "examplesec"}, GET)
        self.assertEqual([j.title for j in jobs], ["SOC Analyst Intern", "Security Engineer Intern"])

    def test_smartrecruiters_with_details(self):
        jobs = smartrecruiters.fetch({"name": "Example Shop", "slug": "exampleshop"}, GET)
        self.assertEqual(len(jobs), 2)
        self.assertIn("Indonesia", jobs[0].location)
        self.assertEqual(jobs[0].text, "")
        smartrecruiters.details(jobs[0], GET)
        self.assertIn("Power BI", jobs[0].text)
        self.assertTrue(jobs[0].url.endswith("9001-intern-data-analytics"))


class TestFilter(unittest.TestCase):
    def test_internship_titles(self):
        for t in ["Cyber Security Intern", "Magang IT Support", "Internship - SOC", "Intern [GIP] - Tech Engineering",
                  "IT Trainee", "Graduate Program 2027"]:
            self.assertTrue(is_internship(t), t)
        for t in ["Senior Engineer", "Internal Audit Manager", "International Sales"]:
            self.assertFalse(is_internship(t), t)

    def test_locations(self):
        self.assertEqual(location_match("Kecamatan Setiabudi id"), "jakarta")
        self.assertEqual(location_match("BSD City, Tangerang"), "jakarta")
        self.assertEqual(location_match("Indonesia"), "indonesia")
        self.assertEqual(location_match("Bandung, Indonesia"), "")
        self.assertEqual(location_match("Singapore"), "")

    def test_keep(self):
        self.assertTrue(keep(job("Cyber Security Intern", "Jakarta, Indonesia")))
        self.assertTrue(keep(job("Magang IT Support", "Jakarta Selatan")))
        self.assertFalse(keep(job("Senior Engineer", "Jakarta")))
        self.assertFalse(keep(job("Software Engineer Intern", "Singapore")))
        self.assertFalse(keep(job("Global Trainee Program 2027 (Hong Kong based)", "Jakarta")))
        self.assertTrue(keep(job("IT Intern", "Bandung"), extra_places=("Bandung",)))


class TestScore(unittest.TestCase):
    def scored(self, j, risk="low"):
        j.ghost_risk = risk
        score(j, {"max_months": 3}, now=NOW)
        return j

    def test_cyber_beats_tech_beats_other(self):
        c = self.scored(job("Cyber Security Intern"))
        t = self.scored(job("Software Engineer Intern"))
        o = self.scored(job("Marketing Intern"))
        self.assertEqual((c.category, t.category, o.category), ("cyber", "tech", "other"))
        self.assertGreater(c.score, t.score)
        self.assertGreater(t.score, o.score)

    def test_cyber_from_description(self):
        j = self.scored(job("IT Intern", text="You will support our SOC analyst team with incident response."))
        self.assertEqual(j.category, "cyber")

    def test_six_month_role_flagged(self):
        j = self.scored(job("IT Intern", text="This is a 6-month internship."))
        self.assertEqual(j.timing, "long")
        self.assertTrue(any("6 months" in f for f in j.flags))
        short = self.scored(job("IT Intern", text="3 month internship, start immediately"))
        self.assertEqual(short.timing, "good")
        self.assertGreater(short.score, j.score)

    def test_month_names(self):
        self.assertEqual(month_ranges("Be a part of an exciting internship from Jan - June 2027."), [(1, 2027, 6)])
        self.assertEqual(month_ranges("Desember 2026 sampai Februari 2027"), [(12, 2026, 3)])
        j = self.scored(job("Tech Intern", text="Internship from Jan - June 2027"))
        self.assertEqual(j.timing, "long")
        later = self.scored(job("Tech Intern", text="Programme runs Jun - Aug 2027"))
        self.assertEqual(later.timing, "later")

    def test_flags(self):
        j = self.scored(job("IT Intern", text="Requires surat pengantar from your campus. 2+ years of experience."))
        self.assertTrue(any("letter" in f for f in j.flags))
        self.assertTrue(any("years of experience" in f for f in j.flags))

    def test_ghost_risk_lowers_score(self):
        self.assertGreater(self.scored(job("IT Intern")).score, self.scored(job("IT Intern"), risk="high").score)


class TestGhost(unittest.TestCase):
    def test_fresh_company_posting_is_low(self):
        j = job(posted_days=2)
        ghost.assess(j, now=NOW)
        self.assertEqual(j.ghost_risk, "low")

    def test_old_posting_is_high(self):
        j = job(posted_days=70)
        ghost.assess(j, now=NOW)
        self.assertEqual(j.ghost_risk, "high")
        self.assertIn("Posted 70 days ago", j.ghost_reasons)

    def test_medium_age(self):
        j = job(posted_days=40)
        ghost.assess(j, now=NOW)
        self.assertEqual(j.ghost_risk, "medium")

    def test_talent_pool_title_is_high(self):
        j = job("Talent Pool - Internship", posted_days=1)
        ghost.assess(j, now=NOW)
        self.assertEqual(j.ghost_risk, "high")

    def test_talent_pool_in_text_is_medium(self):
        j = job("Intern [GIP] - Corporate Functions", text="Join our Corporate Functions talent pool.", posted_days=1)
        ghost.assess(j, now=NOW)
        self.assertEqual(j.ghost_risk, "medium")


class TestHistory(unittest.TestCase):
    def test_new_then_seen_then_repost(self):
        h = {"roles": {}}
        a = job("SOC Intern", id="gh:1")
        history.update(h, [a], now=NOW, fetched_companies={"Acme"})
        self.assertTrue(a.is_new)

        a2 = job("SOC Intern", id="gh:1")
        history.update(h, [a2], now=NOW + timedelta(days=1), fetched_companies={"Acme"})
        self.assertFalse(a2.is_new)

        closed = history.update(h, [], now=NOW + timedelta(days=2), fetched_companies={"Acme"})
        self.assertEqual(closed[0]["ids"], ["gh:1"])

        b = job("SOC Intern", id="gh:2")  # same role, new posting id after it closed
        history.update(h, [b], now=NOW + timedelta(days=5), fetched_companies={"Acme"})
        self.assertEqual(b.reposts, 1)
        ghost.assess(b, now=NOW + timedelta(days=5))
        self.assertEqual(b.ghost_risk, "medium")
        self.assertIn("Taken down and reposted", b.ghost_reasons)

    def test_failed_board_not_marked_closed(self):
        h = {"roles": {}}
        history.update(h, [job("SOC Intern", id="gh:1")], now=NOW, fetched_companies={"Acme"})
        closed = history.update(h, [], now=NOW + timedelta(days=1), fetched_companies=set())
        self.assertEqual(closed, [])


class TestDigest(unittest.TestCase):
    def rows(self):
        base = dict(location="Jakarta", url="https://e.x", flags=[], score=50, timing="good", ghost_risk="low")
        return [
            dict(base, title="Old Cyber Intern", company="A", is_new=False, category="cyber"),
            dict(base, title="New Tech Intern", company="B", is_new=True, category="tech"),
            dict(base, title="New Cyber Intern", company="C", is_new=True, category="cyber", score=40),
            dict(base, title="New Ghost Intern", company="D", is_new=True, category="cyber", ghost_risk="high"),
            dict(base, title="New Marketing Intern", company="E", is_new=True, category="other"),
            dict(base, title="New Later Intern", company="F", is_new=True, category="tech", timing="later"),
        ]

    def test_only_new_relevant_jobs(self):
        msg = digest.build(self.rows(), env={})
        self.assertEqual(msg["count"], 2)
        self.assertLess(msg["text"].index("New Cyber Intern"), msg["text"].index("New Tech Intern"))
        for absent in ("Old Cyber", "Ghost", "Marketing", "Later"):
            self.assertNotIn(absent, msg["text"])

    def test_tracker_url_from_repo(self):
        self.assertEqual(digest.tracker_url({"GITHUB_REPOSITORY": "Someone/Job-Search-Tool"}),
                         "https://someone.github.io/Job-Search-Tool/")

    def test_delivery_channels(self):
        msg = digest.build(self.rows(), env={})
        sent = {}

        class FakeResp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self, *a): return b'{"ok": true}'

        def opener(req, timeout=0):
            sent["telegram"] = req.data.decode()
            return FakeResp()

        class FakeSMTP:
            def __init__(self, host, port, timeout=0): sent["smtp"] = (host, port)
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def starttls(self, context=None): pass
            def login(self, u, p): sent["login"] = u
            def send_message(self, m): sent["email"] = m["Subject"]

        env = {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "1", "SMTP_HOST": "smtp.example.com",
               "SMTP_USER": "u", "SMTP_PASSWORD": "p", "ALERT_EMAIL_TO": "to@example.com"}
        self.assertTrue(digest.send_telegram(msg, env=env, opener=opener))
        self.assertIn("New+Cyber+Intern", sent["telegram"])
        self.assertTrue(digest.send_email(msg, env=env, smtp_cls=FakeSMTP))
        self.assertEqual(sent["smtp"], ("smtp.example.com", 587))
        self.assertFalse(digest.send_telegram(msg, env={}))
        self.assertEqual(digest.deliver(dict(msg, count=0), env=env), [])


class TestEndToEnd(unittest.TestCase):
    def test_offline_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(offline=True, companies=None, profile=str(ROOT / "config" / "profile.json"),
                                      out=tmp, send_alert=False, check_links=False, top=0)
            res = cli.run(args, now=NOW)
            titles = [j["title"] for j in res["jobs"]]
            self.assertEqual(titles[0], "Cyber Security Intern")
            self.assertIn("Magang IT Support", titles)
            self.assertNotIn("Senior Backend Engineer", titles)
            self.assertNotIn("Software Engineer Intern", titles)  # Singapore
            self.assertNotIn("Intern, Finance", titles)  # Bandung
            missing = [s for s in res["sources"] if not s["ok"]]
            self.assertEqual(sorted(s["company"] for s in missing), ["Job-alert emails", "Missing Co"])
            soc = next(j for j in res["jobs"] if j["title"] == "SOC Analyst Intern")
            self.assertEqual(soc["ghost_risk"], "high")
            saved = json.loads((Path(tmp) / "jobs.json").read_text())
            self.assertEqual(saved["counts"]["internships"], len(titles))
            self.assertTrue((Path(tmp) / "jobs.csv").exists())
            self.assertIn("new internship", (Path(tmp) / "digest.md").read_text())

            # Second run a day later: nothing is new, nothing closed.
            res2 = cli.run(args, now=NOW + timedelta(days=1))
            self.assertEqual(res2["counts"]["new"], 0)
            self.assertEqual(res2["closed"], [])


class TestHtml(unittest.TestCase):
    def test_html_to_text(self):
        self.assertEqual(html_to_text("&lt;p&gt;Hi &amp;amp; bye&lt;/p&gt;"), "Hi & bye")


if __name__ == "__main__":
    unittest.main()
