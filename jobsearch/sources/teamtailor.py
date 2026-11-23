"""Teamtailor career sites publish an RSS feed of open jobs: https://<slug>.teamtailor.com/jobs.rss"""

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from ..models import Job, html_to_text

FEED = "https://{slug}.teamtailor.com/jobs.rss"
TT = "{https://teamtailor.com/locations}"


def fetch(company: dict, client) -> list:
    root = ET.fromstring(client.get_text(FEED.format(slug=company["slug"]), polite=False))
    jobs = []
    for item in root.iter("item"):
        locs = [el.text or "" for el in item.iter() if el.tag.endswith("city") or el.tag.endswith("country")]
        remote = (item.findtext("remoteStatus") or "") + " " + " ".join(
            el.text or "" for el in item.iter() if el.tag.lower().endswith("remotestatus"))
        if "fully" in remote.lower() or "remote" in remote.lower():
            locs.append("Remote")
        if "hybrid" in remote.lower():
            locs.append("Hybrid")
        try:
            posted = parsedate_to_datetime(item.findtext("pubDate")).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            posted = None
        link = item.findtext("link") or ""
        jobs.append(Job(
            id=f"teamtailor:{company['slug']}:{item.findtext('guid') or link}",
            title=(item.findtext("title") or "").strip(),
            company=company["name"],
            location=", ".join(dict.fromkeys(x.strip() for x in locs if x and x.strip())),
            url=link,
            source="teamtailor",
            posted_at=posted,
            text=html_to_text(item.findtext("description") or ""),
        ))
    return jobs
