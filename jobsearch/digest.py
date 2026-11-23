"""Daily alert: new, well-matched, not-ghosty internships. Sent by Telegram and/or email.

Configuration comes from environment variables (GitHub repository secrets in the workflow):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID                     -> Telegram message
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO -> email (SMTP over TLS)
  TRACKER_URL (optional) -> link to the tracker page; derived from GITHUB_REPOSITORY if unset
"""

from __future__ import annotations

import html
import json
import os
import smtplib
import ssl
import urllib.parse
import urllib.request
from email.message import EmailMessage

MAX_ITEMS = 15


def pick(jobs: list) -> list:
    new = [j for j in jobs if j.get("is_new") and j.get("category") in ("cyber", "tech")
           and j.get("ghost_risk") != "high" and j.get("timing") != "later"]
    # Cyber first, roles that fit his break before longer ones, then by score.
    new.sort(key=lambda j: (j.get("category") != "cyber", j.get("timing") == "long", -j.get("score", 0)))
    return new


def tracker_url(env=os.environ) -> str:
    if env.get("TRACKER_URL"):
        return env["TRACKER_URL"]
    repo = env.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner.lower()}.github.io/{name}/"
    return ""


def build(jobs: list, first_run: bool = False, env=os.environ) -> dict:
    """Return {'count', 'markdown', 'text', 'html'} for the alert."""
    items = pick(jobs)
    shown = items[:MAX_ITEMS]
    url = tracker_url(env)
    head = (f"{len(items)} new internship{'s' if len(items) != 1 else ''} (Jakarta + remote)"
            + (" (first run: everything counts as new)" if first_run else ""))
    md = [f"# {head}", ""]
    txt = [head, ""]
    htm = [f"<b>{html.escape(head)}</b>", ""]
    for j in shown:
        tag = "🔐 Cyber" if j["category"] == "cyber" else "💻 Tech"
        risk = {"low": "", "medium": " · ⚠️ check ghost risk"}.get(j["ghost_risk"], "")
        flags = f" · {j['flags'][0]}" if j.get("flags") else ""
        place = "Remote" if j.get("where") == "remote" else j['location'].split(';')[0]
        line = f"{tag} · {j['title']} — {j['company']} ({place}){risk}{flags}"
        md.append(f"- [{j['title']} — {j['company']}]({j['url']}) · {tag}{risk}{flags}")
        txt.append(f"- {line}\n  {j['url']}")
        htm.append(f"{html.escape(tag)} · <a href=\"{html.escape(j['url'])}\">{html.escape(j['title'])}</a> — "
                   f"{html.escape(j['company'])}{html.escape(risk + flags)}")
    if len(items) > len(shown):
        more = f"…and {len(items) - len(shown)} more in the tracker."
        md.append(more); txt.append(more); htm.append(html.escape(more))
    if url:
        md += ["", f"Tracker: {url}"]; txt += ["", f"Tracker: {url}"]
        htm += ["", f"<a href=\"{html.escape(url)}\">Open the tracker</a> (follow-ups are under “Needs action”)"]
    return {"count": len(items), "markdown": "\n".join(md) + "\n", "text": "\n".join(txt),
            "html": "\n".join(htm), "subject": head}


def send_telegram(msg: dict, env=os.environ, opener=urllib.request.urlopen) -> bool:
    token, chat = env.get("TELEGRAM_BOT_TOKEN"), env.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return False
    body = msg["html"]
    if len(body) > 4000:
        body = body[:3990].rsplit("\n", 1)[0] + "\n…"
    data = urllib.parse.urlencode({"chat_id": chat, "text": body, "parse_mode": "HTML",
                                   "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with opener(req, timeout=20) as resp:
        return json.load(resp).get("ok", False)


def send_email(msg: dict, env=os.environ, smtp_cls=smtplib.SMTP) -> bool:
    host, to = env.get("SMTP_HOST"), env.get("ALERT_EMAIL_TO")
    user, password = env.get("SMTP_USER"), env.get("SMTP_PASSWORD")
    if not (host and to and user and password):
        return False
    em = EmailMessage()
    em["Subject"] = msg["subject"]
    em["From"] = env.get("ALERT_EMAIL_FROM", user)
    em["To"] = to
    em.set_content(msg["text"])
    with smtp_cls(host, int(env.get("SMTP_PORT", "587")), timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(user, password)
        s.send_message(em)
    return True


def deliver(msg: dict, env=os.environ) -> list:
    """Send through every configured channel. Returns the channels that worked."""
    sent = []
    if msg["count"] == 0:
        return sent
    for name, fn in (("telegram", send_telegram), ("email", send_email)):
        try:
            if fn(msg, env=env):
                sent.append(name)
        except Exception as e:  # never fail the daily run because an alert failed
            print(f"  ! {name} alert failed: {e}")
    return sent
