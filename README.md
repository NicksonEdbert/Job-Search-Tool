# Internship Finder: Jakarta · cybersecurity first, then any tech role

Finds internships in Jakarta, puts cybersecurity roles first and other tech roles next, flags likely **ghost listings**, and gives you a phone-friendly tracker with **skill matching**, **follow-up reminders**, and a daily **Telegram/email alert** of new roles.

- **Automatic listings** come from companies' own public hiring pages (Greenhouse, Lever, Ashby, SmartRecruiters): currently 21 companies, including Grab, Xendit, Stockbit, Blibli, JULO, Binance and OKX. Edit `config/companies.json` to add more.
- **LinkedIn, Glints, JobStreet, Kalibrr, Dealls, Indeed** don't allow tools to read their listings, so the tracker has one-click searches already set to Jakarta, internships and newest first. Anything found there can be added with **“+ Add a job from a link”**.
- Nothing personal is stored in this repo. Skills, statuses and notes stay in the browser of whoever uses the tracker (export/import to move them).

## Quick start (laptop)

Needs Python 3.9+ and nothing else.

```bash
python -m jobsearch                 # fetch, rank, write data/jobs.json + data/jobs.csv
python -m http.server 8000          # then open http://localhost:8000/tracker/
```

`python -m jobsearch --offline` runs on built-in sample data (no internet). Tests: `python -m unittest discover tests`.

## Put it online (so it works on a phone)

The workflow in `.github/workflows/refresh.yml` runs every morning (05:17 Jakarta time). It fetches new listings, commits `data/`, sends the alert, and publishes the tracker to GitHub Pages.

1. Merge this branch into `main` (scheduled runs only happen on the default branch).
2. **Settings → General → Danger Zone → Change visibility → Public** (free GitHub Pages needs a public repo). Only code and public job postings are in the repo.
3. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. **Actions → Daily internship refresh → Run workflow** once. The tracker appears at `https://<your-username>.github.io/<repo-name>/`.

## Daily alert (optional, about 5 minutes)

Add these under **Settings → Secrets and variables → Actions → New repository secret**. Set up Telegram, email, or both.

**Telegram** (easiest on a phone)
1. In Telegram, message **@BotFather** → `/newbot` → copy the token → secret `TELEGRAM_BOT_TOKEN`.
2. Send any message to your new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `"chat":{"id": …}` → secret `TELEGRAM_CHAT_ID`.

**Email** (e.g. Gmail: turn on 2-Step Verification, then create an *App password*)
- `SMTP_HOST` = `smtp.gmail.com`, `SMTP_PORT` = `587`, `SMTP_USER` = the sending address, `SMTP_PASSWORD` = the app password, `ALERT_EMAIL_TO` = who gets the alert.

The alert lists only roles that are **new since yesterday**, cyber and tech only, with high ghost risk and later-start programmes left out. If nothing is new, nothing is sent.

## How ranking works

| Signal | Effect |
|---|---|
| Cybersecurity role (SOC, pentest, GRC, IT audit, incident response, AppSec, …) | biggest boost |
| Other tech role (software, data, QA, DevOps, network, IT support, …) | boost |
| Fits a Dec–Feb break (`max_months` in `config/profile.json`) | boost; 6+ months is labelled *Longer than his break*, later programmes *Starts later* |
| Posted in the last 7/14/30 days | boost |
| Asks for years of experience | penalty |
| Ghost risk medium / high | penalty |

**Ghost risk** is an estimate, not a verdict. It goes up when a posting is over 30/60 days old, sits open for months, is taken down and reposted (tracked in `data/history.json` across daily runs), uses talent-pool / “future opportunities” wording, or isn't from the company's own hiring page. Postings that disappear from a company's board are marked **Closed** in the tracker.

## Tracker features

- **Jobs:** filters (cyber only, fits the break, new since last visit, hide high ghost risk), statuses (Saved → Applied → Interview → Offer / Rejected), notes.
- **Follow-up reminders:** 7 days after *Applied* with no update, the job shows a follow-up prompt with a ready-to-copy message in English and Bahasa Indonesia. It's also listed under *Needs action*.
- **My skills:** type the skills or import a `{"skills": [...]}` file. Each job then shows ✓ matched and ✗ missing skills, and *Skills to learn next* lists the most-requested gaps.
- **Experience:** CTFs, bug bounty, free courses and certifications, Jakarta communities. Edit `config/experience.json`; links are checked daily.
- **Backup:** export/import everything as a JSON file.

## Adding companies

Find the company's job board URL and add a line to `config/companies.json`:

| Board URL looks like | `ats` | `slug` |
|---|---|---|
| `boards.greenhouse.io/<slug>` or `job-boards.greenhouse.io/<slug>` | `greenhouse` | `<slug>` |
| `jobs.lever.co/<slug>` | `lever` | `<slug>` |
| `jobs.ashbyhq.com/<slug>` | `ashby` | `<slug>` |
| `jobs.smartrecruiters.com/<slug>` | `smartrecruiters` | `<slug>` |

Boards that fail to load are listed in the run output and on the tracker's *Backup & settings* tab, and they never stop the run.

## Apply-fast checklist

1. Apply within 24–48 hours of a posting going up; early applicants get far more replies.
2. Keep a one-page CV with a **Projects** section (CTFs, scripts, extensions) near the top.
3. Put a GitHub link with 2–3 small, documented projects on the CV.
4. Message the recruiter or a team member on LinkedIn after applying.
5. Follow up after 7 days (the tracker reminds you).
