# Xavier OC — Developer Portfolio

A production-grade portfolio web application built entirely in Python and Flask. Fully deployed, database-backed, and maintained without touching code — through a custom admin dashboard. Exposes all project data through a versioned public REST API. Ships with automated tests and a CI/CD pipeline.

**Live site → [xavieroc.dev](https://xavieroc.dev)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**API → [xavieroc.dev/api/v1/projects](https://xavieroc.dev/api/v1/projects)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**API docs → [xavieroc.dev/api](https://xavieroc.dev/api)**

Most developer portfolios are static HTML pages or no-code website builders. This one is a full-stack web application — the same kind of system you would build professionally. It handles authentication, database reads and writes, file uploads, form validation, spam protection, email notifications, and automated deployment.

The portfolio itself is the proof of skill.

---

## Table of Contents

0. [Prerequisites](#0-prerequisites)
1. [Quick start](#1-quick-start)
2. [Local vs production](#2-local-vs-production)
3. [Usage](#3-usage)
4. [Data flow](#4-data-flow)
5. [Features](#5-features)
6. [Route map](#6-route-map)
7. [Architecture](#7-architecture)
8. [Module reference](#8-module-reference)
9. [Data schema](#9-data-schema)
10. [Environment variables](#10-environment-variables)
11. [Deploy to Railway](#11-deploy-to-railway)
12. [CI/CD pipeline](#12-cicd-pipeline)
13. [Design decisions](#13-design-decisions)
14. [Dependencies](#14-dependencies)

---

## 0. Prerequisites

- Python 3.11+
- pip
- Docker + Docker Compose (optional — for the containerised local stack)
- A [Railway](https://railway.app) account for production deployment
- A [GitHub](https://github.com) account with this repo pushed (for CI/CD and snapshot auto-commits)

A local PostgreSQL instance is not required — the app falls back to SQLite automatically when `DATABASE_URL` is not set.

---

## 1. Quick start

```bash
git clone https://github.com/xavier-oc-programming/personal_portfolio.git  # download the repo
cd personal_portfolio                                                         # enter the project folder
python -m venv .venv                                                          # create an isolated Python environment
source .venv/bin/activate      # Windows: .venv\Scripts\activate              # activate it
pip install -r requirements.txt                                               # install all dependencies
cp .env.example .env           # then open .env and fill in SECRET_KEY and ADMIN_PASSWORD
python -m app.app                                                             # start the development server
```

Open `http://127.0.0.1:5000`. Admin panel at `http://127.0.0.1:5000/admin/login`.

To seed the database with all projects:

```bash
python -m app.seed_projects    # reads admin_snapshot.json and populates the database
```

**Docker alternative — full stack in one command:**

```bash
docker compose up --build      # builds the image, starts the app + PostgreSQL, seeds the database
```

App available at `http://localhost:8000`. Database seeded automatically on first boot.

---

## 2. Local vs production

| | Local (dev) | Railway (production) |
|---|---|---|
| Server | Flask built-in | Gunicorn (`wsgi:app`) |
| Database | SQLite (auto-created) | PostgreSQL (Railway managed) |
| Config | `.env` file | Environment variables on Railway |
| `DATABASE_URL` set? | No — SQLite fallback | Yes — PostgreSQL connection string |
| Entry point | `python -m app.app` | `entrypoint.sh` → `gunicorn wsgi:app` |
| Seed on startup | Manual (`python -m app.seed_projects`) | Automatic (entrypoint runs seeder) |
| GitHub auto-commit | Only if `GITHUB_TOKEN` set | Always active |

---

## 3. Usage

**Browse the public site**

```
GET  /                     →  Home — featured projects hero
GET  /projects             →  Full project gallery (filter by category, tag, sort)
GET  /projects/web         →  Web projects pre-filtered
GET  /projects/data        →  Data projects pre-filtered
GET  /projects/software    →  Software projects pre-filtered
GET  /projects/<slug>      →  Individual project detail page
GET  /about                →  Developer profile
GET  /contact              →  Contact form
GET  /api                  →  Interactive API documentation
```

**Admin panel** (password protected)

```
GET   /admin/              →  Dashboard — overview stats
GET   /admin/projects      →  All projects list
GET   /admin/projects/new  →  Create a new project
GET   /admin/projects/<slug>        →  Edit a project
GET   /admin/projects/<slug>/media  →  Media manager (images, videos)
GET   /admin/featured      →  Drag-and-drop featured order
GET   /admin/messages      →  Contact form submissions
GET   /admin/backups       →  Download / restore database snapshots
GET   /admin/tags          →  Tag management
```

**REST API** (public, no auth)

```bash
# All projects — returns the full list
curl https://xavieroc.dev/api/v1/projects

# Filter by category, tag, or featured status
curl https://xavieroc.dev/api/v1/projects?category=web
curl https://xavieroc.dev/api/v1/projects?tag=OOP
curl https://xavieroc.dev/api/v1/projects?featured=true

# Single project — replace slug with any project identifier
curl https://xavieroc.dev/api/v1/projects/snake-game-python

# Taxonomy — all categories or tags with project counts
curl https://xavieroc.dev/api/v1/categories
curl https://xavieroc.dev/api/v1/tags
```

---

## 4. Data flow

Every request to the site follows the same path: it hits a Flask route, goes through whatever checks apply, reads from or writes to the database, and sends back a response.

**Reading data (public site and API)**

```
Browser → Flask route → database query → response
                                              ├── HTML page  (public routes)
                                              └── JSON       (API routes)
```

**Submitting the contact form**

```
Browser → Flask route → spam checks → form validation → save to DB → send email notification → HTML response
                              │
                    honeypot + timing + rate limit
                    (blocks bots before touching the DB)
```

**Admin writes (edit a project, upload media, rename a tag, etc.)**

```
Browser → /admin/* → password check → form validation → write to DB
                                                              │
                                                              ├── commit admin_snapshot.json to GitHub  [skip ci]
                                                              └── write timestamped backup  (keeps last 25)
```

The snapshot commit is what keeps the database recoverable — every admin save is backed up to GitHub automatically.

---

## 5. Features

### Public site
- Project gallery with live client-side filtering by category and tag — no page reloads
- Client-side sorting (A–Z, newest, oldest)
- Animated card entrance on load
- Individual project detail pages with full narrative (problem, solution, challenges, results), tech stack, screenshots gallery, YouTube video embeds, and links
- Contact form with three-layer spam protection: honeypot field, fill-time check, and rate limiting
- Email notifications for new contact submissions via Resend API
- Responsive layout (Bootstrap 5)
- SEO metadata and Open Graph tags
- Google Analytics integration
- Sitemap and robots.txt

### Admin dashboard (`/admin`)
- Password-protected session auth
- Full project CRUD — create, edit, delete with a rich form covering all content fields
- **Fill Form Template** — paste a YAML block and auto-fill every project field instantly
- Media manager per project — upload card images, screenshots (multi-file, drag-to-reorder), and video files; add YouTube embed URLs
- Featured projects — drag-and-drop ordering
- Tag management — create, rename, delete, bulk-assign across projects
- Contact message inbox — view and delete submissions
- Database backups — download JSON snapshots; restore any previous snapshot; auto-backup before every write; keeps last 25

### REST API (`/api/v1`)
Public, read-only, no authentication required. CORS enabled for all `/api/*` routes.

| Endpoint | Filters |
|---|---|
| `GET /api/v1/projects` | `?category=`, `?tag=`, `?featured=true`, `?sort=` |
| `GET /api/v1/projects/<slug>` | — |
| `GET /api/v1/categories` | — |
| `GET /api/v1/tags` | — |

Every response uses a consistent JSON envelope:

```json
{
  "success": true,
  "data": [...],
  "count": 4
}
```

---

## 6. Route map

### Public

```
/                                   GET          Home
/about                              GET          About
/projects                           GET          Project gallery (all)
/projects/web                       GET          Web projects
/projects/data                      GET          Data projects
/projects/software                  GET          Software projects
/projects/<slug>                    GET          Project detail
/contact                            GET POST     Contact form
/api                                GET          API documentation
/robots.txt                         GET          SEO robots file
/sitemap.xml                        GET          SEO sitemap
/favicon.ico                        GET          Favicon redirect
```

### Admin (`/admin`)

```
/admin/login                                    GET POST  Login form
/admin/logout                                   GET       Log out
/admin/                                         GET       Dashboard
/admin/projects                                 GET       Project list
/admin/projects/new                             GET POST  Create project
/admin/projects/<slug>                          GET POST  Edit project
/admin/projects/<slug>/delete                   POST      Delete project
/admin/projects/<slug>/media                    GET       Media manager
/admin/projects/<slug>/media/card               POST      Upload card image
/admin/projects/<slug>/media/screenshot         POST      Upload screenshots
/admin/projects/<slug>/media/screenshots/reorder POST     Reorder screenshots
/admin/projects/<slug>/media/video              POST      Upload video file
/admin/projects/<slug>/media/youtube            POST      Add YouTube URL
/admin/projects/<slug>/media/delete             POST      Delete a media item
/admin/featured                                 GET       Featured order page
/admin/featured/reorder                         POST      Save featured order
/admin/featured/add                             POST      Add project to featured
/admin/featured/remove                          POST      Remove from featured
/admin/messages                                 GET       Contact messages
/admin/messages/<id>/delete                     POST      Delete a message
/admin/backups                                  GET       Backup manager
/admin/backups/restore/<filename>               POST      Restore a snapshot
/admin/tags                                     GET       Tag manager
/admin/tags/add                                 POST      Add tag to projects
/admin/tags/assign                              POST      Set tag assignments
/admin/tags/rename                              POST      Rename a tag
/admin/tags/delete                              POST      Delete a tag
```

### API (`/api/v1`)

```
/api/v1/projects                    GET          All projects
/api/v1/projects/<slug>             GET          Single project
/api/v1/categories                  GET          All categories with counts
/api/v1/tags                        GET          All tags with counts
```

---

## 7. Architecture

```
Browser
  │
  ├── Public routes (app.py)           → Jinja2 templates → HTML
  │     /  /projects  /about  /contact  /api
  │
  ├── Admin routes (admin blueprint)
  │     /admin/*                       → Jinja2 templates → HTML
  │
  └── API routes (api blueprint)
        /api/v1/*                      → JSON responses
```

Three Flask blueprints:

- **Main app** (`app/app.py`) — public-facing routes, contact form, spam protection, snapshot sync
- **Admin blueprint** (`app/admin/`) — password-protected management, media uploads, GitHub auto-commits, backups
- **API blueprint** (`app/api/`) — versioned REST endpoints, JSON envelope helpers

```
app/
├── app.py              Main Flask app — public routes, filters, snapshot sync
├── admin/
│   ├── __init__.py     Blueprint registration
│   ├── forms.py        WTForms form classes
│   └── routes.py       All admin routes — CRUD, media, tags, backups, GitHub commit
├── api/
│   ├── __init__.py     Blueprint registration
│   └── routes.py       REST API endpoints and JSON envelope helpers
├── data/
│   ├── projects.py     Seed data — fallback for projects not in snapshot
│   ├── admin_snapshot.json  Live source of truth — committed on every admin write
│   └── backup/         Timestamped JSON snapshots (last 25 kept)
├── models/
│   └── models.py       SQLAlchemy models — Project, ContactMessage
├── seed_projects.py    Database seeder — runs on every deploy
├── static/
│   ├── css/
│   ├── js/
│   │   ├── main.js             Site-wide UI (navbar, scroll, image modal)
│   │   ├── projects-filter.js  Live filtering engine (fetches /api/v1/projects)
│   │   └── api-docs.js         Try It widget on API docs page
│   ├── images/         Card images, screenshots per project
│   └── videos/         Local video files per project (small clips only)
└── templates/
    ├── components/     Reusable partials (navbar, footer, cards, etc.)
    └── admin/          Admin-only templates

tests/
├── conftest.py             Fixtures (app, client, seeded database)
├── test_public_routes.py   Public route status codes
├── test_admin_routes.py    Auth protection and login flow
└── test_api.py             API responses, envelope shape, filters

.github/workflows/
└── ci.yml              Test on every push/PR · Deploy to Railway on main

Dockerfile              Production container definition
docker-compose.yml      Local full-stack (app + PostgreSQL)
entrypoint.sh           Container startup — runs migrations, seeder, then Gunicorn
railway.toml            Railway build and deploy configuration
wsgi.py                 Gunicorn entry point
```

---

## 8. Module reference

### `app/app.py` — helpers

| Function | Description |
|---|---|
| `_normalize_category(category)` | Strips and lowercases; returns `None` if invalid |
| `_normalize_tag(tag)` | Strips whitespace; returns `None` if empty |
| `_normalize_sort(sort_key)` | Validates sort key against allowed values; defaults to `az` |
| `_apply_database_filters(category, tag)` | Builds SQLAlchemy query with optional category and tag filters |
| `_apply_sort(query, sort_key)` | Applies ordering to a query; returns `(query, sort_key)` |
| `_get_available_tags()` | Returns sorted list of all unique tags across all projects |
| `_get_category_counts()` | Returns dict of category → project count |
| `_build_projects_page_context(...)` | Assembles full context dict for projects page |
| `_normalize_text_input(value)` | Strips and truncates single-line text input |
| `_normalize_message_input(value)` | Strips and truncates multi-line message input |
| `_start_contact_form_timer()` | Records form load time in session |
| `_is_honeypot_triggered(form)` | Returns True if the hidden honeypot field was filled |
| `_is_form_submitted_too_quickly()` | Returns True if form submitted under 3 seconds |
| `_is_rate_limited()` | Returns True if a submission was made within the cooldown window |
| `_mark_contact_submission_time()` | Records submission time in session |
| `_send_contact_notification(...)` | Sends email via Resend API |
| `_sync_from_snapshot(app)` | Syncs the local database from `admin_snapshot.json` on startup |
| `create_app()` | Application factory — configures Flask, registers blueprints, registers routes |

### `app/admin/routes.py` — helpers

| Function | Description |
|---|---|
| `_require_admin(f)` | Decorator — redirects to login if not authenticated |
| `_split_csv(value)` | Converts comma-separated string to a cleaned list |
| `_get_project_static_dir(slug)` | Returns absolute path to a project's static directory |
| `_get_project_video_dir(slug)` | Returns absolute path to a project's video directory |
| `_static_rel(path)` | Returns path relative to the static directory |
| `_save_file(file, dest)` | Saves an uploaded file securely; returns filename |
| `_backup_projects()` | Writes a timestamped JSON snapshot; prunes to last 25 |
| `_github_commit_file(path)` | Commits a single file to GitHub via API |
| `_github_commit_full_snapshot()` | Commits updated `admin_snapshot.json` to GitHub |
| `_get_tag_counts()` | Returns all tags with project counts, sorted alphabetically |

### `app/admin/forms.py`

| Class | Fields | Description |
|---|---|---|
| `ProjectForm` | title, slug, primary_category, short_description, full_description, featured, date, problem, solution, challenges, results, tags, tech_stack, repo_url, live_url, demo_url | Full project create/edit form |
| `CardImageForm` | card_image | Single image upload for project card |
| `ScreenshotForm` | screenshots | Multi-file image upload |
| `VideoForm` | video | Single video file upload |
| `YouTubeForm` | youtube_url | YouTube URL input for embedded video |

### `app/api/routes.py`

| Function | Route | Description |
|---|---|---|
| `get_projects()` | `GET /api/v1/projects` | Returns all projects; supports category, tag, featured, sort filters |
| `get_project(slug)` | `GET /api/v1/projects/<slug>` | Returns a single project by slug |
| `get_categories()` | `GET /api/v1/categories` | Returns all categories with project counts |
| `get_tags()` | `GET /api/v1/tags` | Returns all tags with project counts |

### `app/models/models.py`

| Class | Description |
|---|---|
| `Project` | Portfolio project — stores all content, media paths, and links |
| `ContactMessage` | Contact form submission — name, email, message, timestamp |

---

## 9. Data schema

### `projects`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `slug` | String(100) | Unique, URL identifier |
| `title` | String(200) | Not null |
| `primary_category` | String(50) | `web`, `data`, or `software` |
| `short_description` | String(300) | Used on project cards |
| `full_description` | Text | Shown on detail page |
| `featured` | Boolean | Whether shown in featured section |
| `featured_order` | Integer | Sort order within featured projects |
| `date` | String(20) | `YYYY-MM-DD` format |
| `problem` | Text | Narrative section |
| `solution` | Text | Narrative section |
| `challenges` | Text | Narrative section |
| `results` | Text | Narrative section |
| `tags` | Text | JSON array of tag strings |
| `tech_stack` | Text | JSON array of technology strings |
| `screenshots` | Text | JSON array of relative static paths |
| `videos` | Text | JSON array of static paths or YouTube URLs |
| `card_image` | String(255) | Relative static path |
| `repo_url` | String(255) | GitHub URL |
| `live_url` | String(255) | Live demo URL |
| `demo_url` | String(255) | Additional demo URL |

### `contact_messages`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `name` | String(60) | Not null |
| `email` | String(254) | Not null |
| `message` | Text | Not null |
| `created_at` | DateTime | Auto-set on insert |

---

## 10. Environment variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key — any long random string |
| `ADMIN_PASSWORD` | Yes | Password for `/admin/login` |
| `DATABASE_URL` | No | PostgreSQL connection string — falls back to SQLite if not set |
| `RESEND_API_KEY` | No | Resend API key for contact form email notifications |
| `CONTACT_NOTIFICATION_EMAIL` | No | Email address to receive contact form submissions |
| `SITE_URL` | No | Public base URL — used for SEO metadata and Open Graph tags |
| `SITE_NAME` | No | Site title used in `<title>` tags and metadata |
| `GOOGLE_ANALYTICS_ID` | No | GA4 measurement ID |
| `FLASK_ENV` | No | `development` or `production` — defaults to `development` |
| `GITHUB_TOKEN` | No | Personal access token with repo write permission — enables snapshot auto-commits |
| `GITHUB_REPO` | No | Repository in `owner/repo` format — required alongside `GITHUB_TOKEN` |

Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

---

## 11. Deploy to Railway

1. **Push your code to GitHub** and connect the repo to [railway.app](https://railway.app).

2. **Create a PostgreSQL database** on Railway (New → Database → PostgreSQL). Railway sets `DATABASE_URL` automatically on the service.

3. **Create a Web Service** on Railway (New → Service → GitHub Repo), connect your repo.

4. **Set environment variables** under the service → Variables tab:

   | Variable | Value |
   |---|---|
   | `SECRET_KEY` | Any long random secret string |
   | `ADMIN_PASSWORD` | Your chosen admin password |
   | `GITHUB_TOKEN` | Personal access token with repo write permission |
   | `GITHUB_REPO` | `your-username/personal_portfolio` |

5. Railway reads `railway.toml` and builds using the `Dockerfile`. On every deploy, `entrypoint.sh` runs database migrations and the seeder before starting Gunicorn.

6. **CI/CD** — deployments are triggered automatically by the GitHub Actions pipeline after tests pass. See [CI/CD pipeline](#12-cicd-pipeline).

---

## 12. CI/CD pipeline

Defined in `.github/workflows/ci.yml`.

**On every push and pull request to `main` (code files only):**
1. Spin up a PostgreSQL service container
2. Install dependencies
3. Run the full test suite against the real database

**On push to `main` only (after tests pass):**

4. Pull the latest `admin_snapshot.json` from GitHub — ensures any admin changes made since the triggering commit are included
5. Deploy to Railway via `railway up`

A failed test blocks deployment. The pipeline will not ship broken code.

**Path filters** — the workflow only triggers when these paths change:

```
app/**/*.py                    # any Python file in the app
app/templates/**               # Jinja2 templates
app/static/css/**              # stylesheets
app/static/js/**               # JavaScript
app/static/images/favicon.png  # favicon only — not all images (media commits use [skip ci])
requirements.txt               # dependency changes
Dockerfile                     # container definition
wsgi.py                        # Gunicorn entry point
entrypoint.sh                  # container startup script
railway.toml                   # Railway config
.github/workflows/**           # CI/CD pipeline changes
tests/**                       # test suite changes
```

Data-only commits (snapshots, media uploads) include `[skip ci]` in the commit message and never trigger the workflow.

### Manual deploy

The workflow supports `workflow_dispatch` — trigger a full test + deploy run from GitHub without pushing any code:

1. Go to the GitHub repo → **Actions** tab
2. Select **CI/CD** in the left sidebar
3. Click **Run workflow** → **Run workflow**

Useful after data-only changes (tag renames, snapshot updates) that don't touch code files.

### Snapshot commits and `[skip ci]`

Every admin write automatically commits an updated `admin_snapshot.json` to GitHub with the message `data: update admin snapshot [skip ci]`. The `[skip ci]` flag skips the workflow entirely — no tests, no deploy. These commits are data backups, not code changes. When a real code change triggers the next deploy, the deploy step pulls the latest snapshot (including all admin changes since the last deploy) before uploading to Railway.

To add a `RAILWAY_PORTFOLIO_TOKEN` secret: GitHub repo → Settings → Secrets and variables → Actions → New repository secret. The token must be a **project-level** token from Railway's project settings.

---

## 13. Design decisions

**Why a REST API on a portfolio?**
Separation of concerns. The Jinja2 templates are one consumer of the project data — not the only possible one. The API makes the data layer explicit and independently accessible. It also powers the live client-side filtering on the projects page — the full project list is fetched once on load and all filtering happens in memory with no page reloads.

**Why a custom admin dashboard instead of Flask-Admin or similar?**
Flask-Admin generates a generic CRUD interface. This dashboard is purpose-built for a portfolio — it only exposes what matters (projects, media, tags, messages, backups) in the way that makes sense for this content. It is also a demonstration of building auth-protected admin tooling from scratch.

**Why automated backups before every write?**
The admin is the only interface that modifies production data. A bug in a delete route or an accidental confirmation would be unrecoverable without backups. The backup runs before the write — not after — so a partial failure still leaves a clean snapshot. The last 25 are kept; older ones are pruned automatically.

**Why is `admin_snapshot.json` the authoritative database source?**
On every deploy, `seed_projects.py` restores the database from the snapshot. This means the database is always consistent with the last admin-confirmed state — even after a full Railway teardown and rebuild. The snapshot is committed to GitHub on every admin write, so it's always version-controlled and recoverable.

**Why does the deploy step pull the latest snapshot before uploading?**
The CI/CD workflow is triggered by code changes, not data changes. Between two code pushes, the admin may have committed several snapshot updates tagged `[skip ci]`. Without a `git pull` in the deploy job, the runner would upload the snapshot as of the triggering commit — potentially missing recent admin edits.

**Why YouTube embeds instead of hosting videos directly?**
Video files large enough to be useful exceed Railway's upload limit when bundled via `railway up`. YouTube embeds solve the size problem, load faster for visitors, support fullscreen and mobile natively, and require no storage management. Local video files are still supported for short clips already in the repo.

**Why three-layer spam protection on the contact form?**
A single check is easy to defeat. The honeypot catches bots that fill all fields. The timing check catches bots that submit faster than a human can read. The rate limit prevents repeated submissions from the same session. Together they block spam without requiring a CAPTCHA.

**Why client-side filtering?**
The projects page fetches the full project list once from `/api/v1/projects` on load. Every subsequent filter or sort is instant — no network round-trip, no page reload. This also demonstrates that the API can serve as the data source for a decoupled front end.

---

## 14. Dependencies

| Package | Used in | Purpose |
|---|---|---|
| `Flask` | `app.py`, blueprints | Web framework — routing, request handling, templating |
| `Flask-SQLAlchemy` | `models.py` | ORM — database models and queries |
| `Flask-WTF` | `forms.py`, routes | CSRF-protected form handling |
| `WTForms` | `forms.py` | Form field types and validators |
| `SQLAlchemy` | `models.py` | Core ORM types |
| `gunicorn` | `wsgi.py`, `Dockerfile` | Production WSGI server |
| `psycopg2-binary` | runtime | PostgreSQL adapter for SQLAlchemy |
| `python-dotenv` | `app.py` | Loads `.env` file into environment |
| `resend` | `app.py` | Email delivery for contact form notifications |
| `requests` | `admin/routes.py` | GitHub API calls for snapshot auto-commits |
| `Werkzeug` | `admin/routes.py` | Secure filename handling for uploads |
| `pytest` | `tests/` | Test runner |
| `pytest-flask` | `tests/` | Flask test client fixtures |
| `email-validator` | `forms.py` | WTForms email field validation |
