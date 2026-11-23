# Internship Finder: Jakarta + remote · cybersecurity first, then any tech role

Finds internships in Jakarta and remote internships open to Indonesia, puts cybersecurity roles first and other tech roles next, flags likely **ghost listings**, and gives you a phone-friendly tracker with **skill matching**, **follow-up reminders**, and a daily **Telegram/email alert** of new roles.

Where listings come from (all checked once a day):

| Source | How |
|---|---|
| **Company career pages** | Public job data behind each company's own careers site: Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, Teamtailor, **Workday** (P&G, PwC, Mastercard, Visa…), **SAP SuccessFactors** (EY, Deloitte, Reckitt…), Amazon, and any career page that publishes Google-for-Jobs data. Read politely: `robots.txt` honoured, one request per second per site. |
| **Remote job boards** | Remotive, Arbeitnow, Remote OK (internships only, kept only if open to someone in Indonesia/Asia/worldwide). |
| **Job-alert emails** | Your LinkedIn, JobStreet, Glints, Kalibrr and Indeed alerts, read from a dedicated Gmail (setup below). This is how listings from those sites get in: they don't allow tools to read their websites. |
| **By hand** | One-click pre-filtered searches on the *Other job sites* tab, and **“+ Add a job from a link”**. |

Nothing personal is stored in this repo. Skills, statuses and notes stay in the browser of whoever uses the tracker (export/import to move them).

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

## Job-alert emails: LinkedIn, JobStreet, Glints, Kalibrr, Indeed (about 15 minutes)

1. **Create a new Gmail just for alerts** (e.g. `yourname.jobalerts@gmail.com`). Using a separate inbox means the tool never sees anyone's personal email.
2. In that account: **Google Account → Security → 2-Step Verification → on**, then **App passwords → create** one (name it "internship finder"). Copy the 16-letter password.
3. **Create job alerts** (daily, location *Jakarta*, keywords like `cyber security intern`, `SOC intern`, `IT intern`, `software engineer intern`, `magang IT`):
   - **JobStreet, Glints, Kalibrr, Indeed:** sign up / set the alert email to the new Gmail.
   - **LinkedIn:** create the alerts on his LinkedIn (Jobs → search → *Set alert*, choose *Email*, daily). They go to his main email, so in **that** Gmail add a filter: *From* `jobalerts-noreply@linkedin.com` → *Forward to* the new Gmail (Gmail asks the new inbox to confirm forwarding once).
4. In this repo: **Settings → Secrets and variables → Actions → New repository secret**:
   - `ALERTS_IMAP_USER` = the new Gmail address
   - `ALERTS_IMAP_PASSWORD` = the app password
5. **Actions → Daily internship refresh → Run workflow.** Jobs from the alerts show up in the tracker with a *via LinkedIn alert* (etc.) label.

The inbox is opened **read-only**: nothing is deleted, moved or marked as read. Only each job's title, company, location and a clean link are kept; no email text goes into the repo. Until the secrets are added, the tracker just says this source isn't set up.

## How ranking works

| Signal | Effect |
|---|---|
| Cybersecurity role (SOC, pentest, GRC, IT audit, incident response, AppSec, …) | biggest boost |
| Other tech role (software, data, QA, DevOps, network, IT support, …) | boost |
| Fits a Dec–Feb break (`max_months` in `config/profile.json`) | boost; 6+ months is labelled *Longer than his break*, later programmes *Starts later* |
| In Jakarta (on-site or hybrid) / remote | Jakarta ranks a little above remote |
| Posted in the last 7/14/30 days | boost |
| Asks for years of experience | penalty |
| Ghost risk medium / high | penalty |

**Remote roles** are kept only if they're open to someone in Indonesia: *worldwide*, *APAC/Asia* or *Indonesia* are kept, *US/EU-only* or "must be authorized to work in the US" are dropped, and unclear ones are kept with a "check he can work from Indonesia" note. Set `"include_remote": false` in `config/profile.json` to turn remote roles off.

**Ghost risk** is an estimate, not a verdict. It goes up when a posting is over 30/60 days old, sits open for months, is taken down and reposted (tracked in `data/history.json` across daily runs), uses talent-pool / “future opportunities” wording, or isn't from the company's own hiring page. Postings that disappear from a company's board are marked **Closed** in the tracker.

## Tracker features

- **Jobs:** filters (cyber only, Jakarta / remote, fits the break, new since last visit, hide high ghost risk), statuses (Saved → Applied → Interview → Offer / Rejected), notes.
- **Follow-up reminders:** 7 days after *Applied* with no update, the job shows a follow-up prompt with a ready-to-copy message in English and Bahasa Indonesia. It's also listed under *Needs action*.
- **My skills:** type the skills or import a `{"skills": [...]}` file. Each job then shows ✓ matched and ✗ missing skills, and *Skills to learn next* lists the most-requested gaps.
- **Experience:** CTFs, bug bounty, free courses and certifications, Jakarta communities. Edit `config/experience.json`; links are checked daily.
- **Backup:** export/import everything as a JSON file.

## Adding companies

Quickest: `python tools/discover.py "company name" another-name` tries the name on every supported hiring system and prints which ones answer, with how many Indonesian internships they have.

Or find the company's careers URL and add a line to `config/companies.json`:

| Careers URL looks like | `ats` | `slug` |
|---|---|---|
| `boards.greenhouse.io/<slug>` or `job-boards.greenhouse.io/<slug>` | `greenhouse` | `<slug>` |
| `jobs.lever.co/<slug>` | `lever` | `<slug>` |
| `jobs.ashbyhq.com/<slug>` | `ashby` | `<slug>` |
| `jobs.smartrecruiters.com/<slug>` | `smartrecruiters` | `<slug>` |
| `apply.workable.com/<slug>` | `workable` | `<slug>` |
| `<slug>.recruitee.com` | `recruitee` | `<slug>` |
| `<slug>.teamtailor.com` | `teamtailor` | `<slug>` |
| `<tenant>.wd3.myworkdayjobs.com/<Site>` | `workday` | `<tenant>\|wd3\|<Site>` |
| SAP SuccessFactors site with `/job/<Place>-<Title>/<id>/` links (e.g. `careers.ey.com`) | `successfactors` | the domain |
| Any careers page whose job pages carry Google-for-Jobs data | `jsonld` | the listing page (or sitemap) URL |

Boards that fail to load are listed in the run output and on the tracker's *Backup & settings* tab, and they never stop the run.

## Apply-fast checklist

1. Apply within 24–48 hours of a posting going up; early applicants get far more replies.
2. Keep a one-page CV with a **Projects** section (CTFs, scripts, extensions) near the top.
3. Put a GitHub link with 2–3 small, documented projects on the CV.
4. Message the recruiter or a team member on LinkedIn after applying.
5. Follow up after 7 days (the tracker reminds you).
