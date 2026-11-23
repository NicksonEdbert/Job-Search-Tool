# Work Experience Finder: Jakarta + Melbourne · cybersecurity first, then any tech role

Finds **real-world work experience** for a cybersecurity student in Jakarta or Melbourne (or remote): internships, entry-level and casual IT jobs (service desk, IT support, junior security), student jobs and volunteer roles. It ranks cyber roles first, flags likely **ghost listings** and roles a student visa can't take, and gives you a phone-friendly tracker with **skill matching**, **follow-up reminders**, a **WhatsApp "send to him" button** and an **Opportunities** tab for things that aren't on job boards.

Where listings come from (all checked once a day):

| Source | How |
|---|---|
| **Company career pages** | Public job data behind each company's own careers site: Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, Teamtailor, **Workday** (P&G, PwC, Mastercard, Visa…), **SAP SuccessFactors** (EY, Deloitte, Reckitt…), Amazon, and any career page that publishes Google-for-Jobs data. Read politely: `robots.txt` honoured, one request per second per site. |
| **Remote job boards** | Remotive, Arbeitnow, Remote OK (internships only, kept only if open to someone in Indonesia/Asia/worldwide). |
| **Job-alert emails** | Your LinkedIn, SEEK, JobStreet, Glints, Kalibrr and Indeed alerts, read from a dedicated Gmail (setup below). SEEK alerts are the best source of Melbourne casual IT jobs. This is how listings from those sites get in: they don't allow tools to read their websites. |
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

Job-alert results come from the **search filters** (keywords, Jakarta, internship), not from whose profile they're on. So the person running the tool can set them up on **their own** accounts, and the student doesn't need to do anything.

1. **Create a new Gmail just for alerts** (e.g. `yourname.jobalerts@gmail.com`). Turn on **2-Step Verification** for it, then **Security → App passwords → create** one and copy the 16-letter password.
2. **Create job alerts on your own accounts** (daily; location *Jakarta*; keywords like `cyber security intern`, `SOC intern`, `IT intern`, `software engineer intern`, `magang IT`):
   - **LinkedIn:** Jobs → search → **Set alert** → email, daily.
   - **SEEK (Melbourne), JobStreet, Glints, Kalibrr, Indeed:** save the search / turn on the job alert.
3. **Forward only the alert emails** to the new Gmail. In your own Gmail: **Settings → Filters → Create filter**, put the **exact sender** in *From*, then choose *Forward to* the new Gmail (Gmail asks the new inbox to confirm once).
   - LinkedIn alerts come from `jobalerts-noreply@linkedin.com`.
   - For the other sites, wait for the first alert email and copy its exact sender address into a filter.
   - **Don't forward a whole domain** (e.g. everything from `jobstreet.com`): that would also send password-reset and login-code emails into the alert inbox.
4. In this repo: **Settings → Secrets and variables → Actions → New repository secret**:
   - `ALERTS_IMAP_USER` = the new Gmail address
   - `ALERTS_IMAP_PASSWORD` = the app password
5. **Actions → Daily internship refresh → Run workflow.** Jobs from the alerts show up with a *via LinkedIn alert* (etc.) label.

Please don't create an extra LinkedIn account for this (LinkedIn allows one account per person), and don't make the alerts Gmail the main email on anyone's LinkedIn (their recruiter messages and login codes would go there).

The inbox is opened **read-only**: nothing is deleted, moved or marked as read. Only each job's title, company, location and a clean link are kept; no email text goes into the repo. Until the secrets are added, the tracker just says this source isn't set up.

## Running it for someone else (WhatsApp)

If you're helping a family member or friend, they don't need to use the tool at all:

1. In the tracker, tick **Send** on the good jobs. A bar appears at the bottom.
2. Tap **Send on WhatsApp**. WhatsApp opens with a ready message: each job's title, company, *why it fits* (cyber/tech, fits the break, fresh posting), any warning (e.g. "asks for 6 months"), and the apply link. **Share ↗** on a card sends just that one job.
3. Sent jobs get a *Sent to him* badge and their own filter, so nothing is sent twice.

Put their WhatsApp number (with country code) under **Backup & settings**; it's saved only in your browser, never in the repo. The message can be in English or Bahasa Indonesia.

### Handing it over later

When they want to use it themselves: open the tracker link on their phone (Share → *Add to Home Screen*). A short "How to use this" card appears the first time. To give them everything you've tracked, tap **Export backup**, send them the file, and they tap **Import backup**. Their alerts can move to their own accounts the same way as step 2–3 above; nothing in the tool changes.

## Real-world work this break (Opportunities tab)

Advertised internships are scarce in December, so the tracker also covers the other ways students get experience:

- **Student jobs (Melbourne):** Monash Jobs for Students, Career Connect, the student jobs board and the Monash Student Association.
- **Volunteering:** SEEK Volunteer, Pro Bono Australia, Red Cross IT service desk, Be Connected digital mentors; in Jakarta Relawan TIK, Indorelawan, Siberkreasi.
- **Companies to contact directly:** managed IT and cyber firms in both cities, plus **+ Add** for family contacts.
- **Small paid jobs:** a ready "IT & security check-up" offer for small businesses, a checklist, and a CV line.
- **Ready messages** (English / Bahasa): cold email (Melbourne asks for paid work, Jakarta says unpaid is fine), LinkedIn note, volunteer enquiry, WhatsApp to family, follow-ups.

Each item has a status (Contacted / Applied / Replied / Doing it), notes and a 7-day follow-up reminder. Everything is saved in the browser and included in **Export backup**. Edit `config/opportunities.json` to add more; links are checked daily.

**Rules worth knowing in Australia:** on a student visa he can usually work **unlimited hours during official course breaks** (check VEVO / Monash's visa page). Internships should be **paid** unless they're part of his course; volunteering for genuine non-profits is fine. Roles that need Australian citizenship, permanent residency or a security clearance are hidden; "full working rights" ones are flagged.

## How ranking works

| Signal | Effect |
|---|---|
| Cybersecurity role (SOC, pentest, GRC, IT audit, incident response, AppSec, …) | biggest boost |
| Other tech role (software, data, QA, DevOps, network, IT support, …) | boost |
| Fits a Dec–Feb break (`max_months` in `config/profile.json`) | boost; 6+ months is labelled *Longer than his break*, later programmes *Starts later* |
| In Jakarta or Melbourne (on-site or hybrid) / remote | both cities rank the same, remote a little lower |
| Permanent full-time "junior" job | flagged: ask if casual or summer-only work is possible |
| Posted in the last 7/14/30 days | boost |
| Asks for years of experience | penalty |
| Ghost risk medium / high | penalty |

**Remote roles** are kept only if they're open to someone in Indonesia: *worldwide*, *APAC/Asia* or *Indonesia* are kept, *US/EU-only* or "must be authorized to work in the US" are dropped, and unclear ones are kept with a "check he can work from Indonesia" note. Set `"include_remote": false` in `config/profile.json` to turn remote roles off.

**Ghost risk** is an estimate, not a verdict. It goes up when a posting is over 30/60 days old, sits open for months, is taken down and reposted (tracked in `data/history.json` across daily runs), uses talent-pool / “future opportunities” wording, or isn't from the company's own hiring page. Postings that disappear from a company's board are marked **Closed** in the tracker.

## Tracker features

- **Jobs:** filters (cyber only, Jakarta / Melbourne / remote, type: internship / entry-level & casual / student job / volunteer, fits the break, new since last visit, hide high ghost risk), statuses (Saved → Applied → Interview → Offer / Rejected), notes.
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
