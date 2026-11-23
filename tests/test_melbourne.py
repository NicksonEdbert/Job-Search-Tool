import argparse
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from jobsearch import cli
from jobsearch.filter import au_work_rights, keep, location_match, role_type
from jobsearch.models import Job
from jobsearch.score import score

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parent.parent


def job(title, location="Melbourne, VIC", text=""):
    return Job(id=f"t:{title}:{location}", title=title, company="X", location=location, url="https://e.x",
               source="greenhouse", text=text)


class TestRoleTypes(unittest.TestCase):
    def test_types(self):
        cases = {
            "Cyber Security Intern": "internship", "Summer Vacation Program 2026/27": "internship",
            "IT Support Officer (Casual)": "entry", "Junior SOC Analyst": "entry", "Service Desk Analyst": "entry",
            "Student IT Support": "student", "Peer Mentor": "student", "Volunteer IT Helper": "volunteer",
            "Relawan TIK": "volunteer",
        }
        for title, expected in cases.items():
            self.assertEqual(role_type(title), expected, title)
        for title in ("Senior Service Desk Analyst", "SOC Team Lead", "Security Architect", "Marketing Manager",
                      "Software Engineer III"):
            self.assertIsNone(role_type(title), title)

    def test_junior_in_name_only_is_dropped(self):
        self.assertFalse(keep(job("Junior SOC Analyst", text="Requires 4+ years of experience")))
        self.assertTrue(keep(job("Junior SOC Analyst", text="1 year of experience is a plus")))

    def test_role_types_can_be_switched_off(self):
        self.assertFalse(keep(job("Volunteer IT Helper"), role_types=("internship", "entry")))


class TestMelbourne(unittest.TestCase):
    def test_locations(self):
        self.assertEqual(location_match("Melbourne, VIC, Australia"), "melbourne")
        self.assertEqual(location_match("Clayton, Victoria, Australia"), "melbourne")
        self.assertEqual(location_match("Richmond VIC"), "melbourne")
        self.assertEqual(location_match("Richmond, VA"), "")
        self.assertEqual(location_match("Victoria, BC"), "")
        self.assertEqual(location_match("Sydney, NSW"), "")
        self.assertEqual(location_match("Melbourne", cities=("jakarta",)), "")
        self.assertEqual(location_match("Jakarta", cities=("melbourne",)), "")

    def test_work_rights(self):
        self.assertEqual(au_work_rights(job("Graduate Analyst", text="Must be an Australian citizen."))[0], "blocked")
        self.assertEqual(au_work_rights(job("Analyst", text="Ability to obtain a Baseline security clearance"))[0], "blocked")
        self.assertEqual(au_work_rights(job("Analyst", text="Open to Australian citizens and permanent residents only"))[0],
                         "blocked")
        self.assertEqual(au_work_rights(job("Analyst", text="You need full working rights in Australia"))[0], "flag")
        self.assertEqual(au_work_rights(job("Analyst", text="We welcome international students"))[0], "ok")
        self.assertFalse(keep(job("Graduate Cyber Analyst", text="NV1 clearance required")))
        self.assertTrue(keep(job("Graduate Cyber Analyst", text="Great team")))

    def test_remote_open_to_australia(self):
        self.assertTrue(keep(job("Security Intern", "Remote (Australia)")))
        self.assertTrue(keep(job("Security Intern", "Remote (APAC)")))

    def test_scoring_flags(self):
        perm = job("IT Support Officer", text="This is a permanent full-time position.")
        score(perm, {}, now=NOW)
        self.assertEqual((perm.where, perm.role_type, perm.timing), ("melbourne", "entry", "check"))
        self.assertTrue(any("Permanent full-time" in f for f in perm.flags))
        casual = job("IT Support Officer (Casual)", text="Casual summer role")
        score(casual, {}, now=NOW)
        self.assertEqual(casual.timing, "good")
        fwr = job("Service Desk Analyst", text="Candidates need full working rights")
        score(fwr, {}, now=NOW)
        self.assertTrue(any("full working rights" in f for f in fwr.flags))
        jkt, mel = job("Security Intern", "Jakarta"), job("Security Intern", "Melbourne")
        score(jkt, {}, now=NOW)
        score(mel, {}, now=NOW)
        self.assertEqual(jkt.score, mel.score)  # both cities rank the same


class TestEndToEndMelbourne(unittest.TestCase):
    def test_offline_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(offline=True, companies=None, profile=str(ROOT / "config" / "profile.json"),
                                      out=tmp, send_alert=False, check_links=False, top=0)
            res = cli.run(args, now=NOW)
            mel = {(j["title"], j["company"]): j for j in res["jobs"] if j["where"] == "melbourne"}
            titles = {t for t, _ in mel}
            for t in ("IT Support Officer (Casual)", "Service Desk Analyst", "IT Support Associate",
                      "Student IT Support (Summer)", "Volunteer Cyber Awareness Educator", "IT Support Officer"):
                self.assertIn(t, titles)
            for t in ("Graduate Cyber Consultant", "Junior SOC Analyst", "Senior Cloud Engineer"):
                self.assertNotIn(t, titles)  # citizenship, 4+ years, senior
            # Richmond, VA is not Melbourne
            self.assertEqual(sum(1 for (t, c) in mel if t == "IT Support Officer" and c == "Example Melbourne Co"), 1)
            types = {mel[k]["role_type"] for k in mel}
            self.assertTrue({"entry", "student", "volunteer"} <= types)
            self.assertGreaterEqual(res["counts"]["melbourne"], 6)
            self.assertIn("by_type", res["counts"])
            # Jakarta results are still there
            self.assertIn("Cyber Security Intern", {j["title"] for j in res["jobs"] if j["where"] == "jakarta"})


if __name__ == "__main__":
    unittest.main()
