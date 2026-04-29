# Xavier OC — Developer Portfolio

A production-grade portfolio web application built entirely in Python and Flask. Fully deployed, database-backed, and maintained without touching code — through a custom admin dashboard. Exposes all project data through a versioned public REST API. Ships with automated tests and a CI/CD pipeline.

**Live site → [xavieroc.dev](https://xavieroc.dev)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**API → [xavieroc.dev/api/v1/projects](https://xavieroc.dev/api/v1/projects)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**API docs → [xavieroc.dev/api](https://xavieroc.dev/api)**

---

## What This Is

Most developer portfolios are static HTML pages or no-code website builders. This one is a full-stack web application — the same kind of system you would build professionally. It handles authentication, database reads and writes, file uploads, form validation, spam protection, email notifications, and automated deployment.

The portfolio itself is the proof of skill.

---

## Feature Overview

### Public Site
| Page | What it does |
|---|---|
| **Home** | Highlights featured projects with a hero section |
| **Projects** | Full project gallery with live filtering by category and tag, client-side sorting, and animated card entrance — no page reloads |
| **Project detail** | Individual project page with full description, tech stack, problem/solution narrative, screenshots, and links |
| **About** | Developer profile and background |
| **Contact** | Contact form with spam protection — honeypot field, fill-time check, and rate limiting |
| **API docs** | Interactive REST API documentation with live Try It widget |

### Admin Dashboard (`/admin`)
Password-protected. The entire portfolio is maintainable through this interface without touching the codebase.

| Section | Capabilities |
|---|---|
| **Projects** | Create, edit, delete projects. Full rich form for all content fields. **Fill Form Template** button parses a pasted YAML block and auto-fills every field instantly |
| **Media manager** | Upload and delete card images, screenshots, and videos per project |
| **Tags** | Create tags, assign them to projects, rename, and delete — with live search and bulk assignment |
| **Messages** | View and delete contact form submissions |
| **Backups** | Download JSON snapshots of the database. Auto-backup triggers before every write operation. Keeps the 25 most recent snapshots |

### REST API (`/api/v1`)
Public, read-only, no authentication required.

| Endpoint | Description |
|---|---|
| `GET /api/v1/projects` | All projects — supports `?category=`, `?tag=`, `?featured=true` |
| `GET /api/v1/projects/<slug>` | Single project by slug |
| `GET /api/v1/categories` | All categories with project counts |
| `GET /api/v1/tags` | All tags with project counts |

Every response uses a consistent JSON envelope:
```json
{
  "success": true,
  "data": [...],
  "count": 4
}
```

CORS is enabled for all `/api/*` routes — the API can be consumed from any origin.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11 |
| **Web framework** | Flask 3.1 |
| **Database ORM** | SQLAlchemy via Flask-SQLAlchemy |
| **Database** | PostgreSQL (production) · SQLite (local dev) |
| **Forms & CSRF** | Flask-WTF + WTForms |
| **Email** | Resend API |
| **Frontend** | Bootstrap 5 · Vanilla JS |
| **Server** | Gunicorn |
| **Deployment** | Railway |
| **Containerisation** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |
| **Testing** | pytest + pytest-flask |

---

## Architecture

```
Browser
  │
  ├── Public routes (Flask)        → Jinja2 templates → HTML
  │     /  /projects  /about  /contact
  │
  ├── Admin routes (Flask blueprint, auth-protected)
  │     /admin/*                  → Jinja2 templates → HTML
  │
  └── API routes (Flask blueprint, public, JSON)
        /api/v1/*                 → JSON responses
```

The application is structured around three Flask blueprints:

- **Main app** (`app/app.py`) — public-facing routes
- **Admin blueprint** (`app/admin/`) — password-protected management interface
- **API blueprint** (`app/api/`) — versioned REST endpoints

The projects page fetches data from the API on load and handles all filtering and sorting client-side — no page reload on category, tag, or sort changes.

```
app/
├── admin/          Admin blueprint (routes, forms)
├── api/            API blueprint (routes, response helpers)
├── data/           Seed data
├── models/         SQLAlchemy models (Project, ContactMessage)
├── static/         CSS, JS, images
│   ├── css/
│   └── js/
│       ├── main.js             Site-wide UI (navbar, scroll-to-top, image modal)
│       ├── projects-filter.js  Live filtering engine (fetches from /api/v1/projects)
│       └── api-docs.js         Try It widget on the API docs page
└── templates/      Jinja2 templates
    ├── components/ Reusable partials (navbar, footer, cards, etc.)
    └── admin/      Admin-only templates

tests/
├── conftest.py             Fixtures (app, client, seeded database)
├── test_public_routes.py   Public route status codes
├── test_admin_routes.py    Auth protection and login flow
└── test_api.py             API responses, envelope shape, filters

.github/workflows/
└── ci.yml                  Test on every push/PR · Deploy to Railway on main

project_fill_template.md    YAML template for generating project entries — scan a repo,
                            fill the template, paste into the admin Fill Form Template modal
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- pip

A local PostgreSQL instance is optional — the app falls back to SQLite automatically when `DATABASE_URL` is not set.

### 1. Clone and install

```bash
git clone https://github.com/xavier-oc-programming/personal_portfolio.git
cd personal_portfolio
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

```env
SECRET_KEY=any-long-random-string    # Required — keeps sessions secure
ADMIN_PASSWORD=your-chosen-password  # Required — protects /admin
```

Everything else is optional for local development. Without `DATABASE_URL`, the app creates a local SQLite database automatically.

### 3. Run

```bash
python -m app.app
```

Open `http://127.0.0.1:5000`. The database tables are created on first run. To seed the database with the default project set:

```bash
python -m app.seed_projects
```

### 4. Admin access

Navigate to `http://127.0.0.1:5000/admin/login` and enter the password you set as `ADMIN_PASSWORD`.

---

## Docker

Run the full application stack — app and database — with a single command.

### Prerequisites
- Docker
- Docker Compose

### Start

```bash
docker compose up --build
```

The app is available at `http://localhost:8000`. On first boot, the entrypoint script seeds the database with all 51 projects automatically — no manual steps required. Data persists in a named volume across restarts.

### Environment

Docker Compose reads `ADMIN_PASSWORD` and `SECRET_KEY` from your `.env` file. Make sure both are set before running.

### Stop

```bash
docker compose down          # Stop containers
docker compose down -v       # Stop and delete the database volume
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key. Any long random string. |
| `ADMIN_PASSWORD` | Yes | Password for `/admin/login`. |
| `DATABASE_URL` | No | PostgreSQL connection string. Falls back to SQLite if not set. |
| `RESEND_API_KEY` | No | Resend API key for contact form email notifications. |
| `CONTACT_NOTIFICATION_EMAIL` | No | Email address to receive contact form submissions. |
| `SITE_URL` | No | Public base URL. Used for SEO metadata and Open Graph tags. |
| `SITE_NAME` | No | Site title used in `<title>` tags and metadata. |
| `GOOGLE_ANALYTICS_ID` | No | GA4 measurement ID for analytics. |
| `FLASK_ENV` | No | `development` or `production`. Defaults to `development`. |
| `GITHUB_TOKEN` | No | Personal access token with repo write permission. Enables automatic snapshot commits to GitHub after every admin write. |
| `GITHUB_REPO` | No | Repository in `owner/repo` format. Required alongside `GITHUB_TOKEN` for snapshot auto-commit. |

---

## Tests

The test suite covers public routes, admin authentication, and all API endpoints. Tests run against SQLite locally and PostgreSQL in CI.

```bash
pytest            # Run all 26 tests
pytest -v         # Verbose output
pytest tests/test_api.py    # Run a specific file
```

### What is tested

**Public routes** — every public page returns 200. A non-existent project slug returns 404.

**Admin routes** — unauthenticated requests to protected routes redirect to login. Login accepts the correct password and rejects the wrong one.

**API endpoints** — every endpoint returns 200 with the correct JSON envelope shape. Filtering by category and featured status works. A missing slug returns 404 with a JSON error body, not an HTML page.

---

## CI/CD Pipeline

Defined in `.github/workflows/ci.yml`.

**On every push and pull request to `main`:**
1. Spin up a PostgreSQL service container
2. Install dependencies
3. Run the full test suite against the real database

**On push to `main` only (after tests pass):**
4. Pull the latest snapshot from GitHub (ensures the most recent admin changes are included)
5. Deploy to Railway automatically

A failed test blocks deployment. The pipeline will not ship broken code.

### Manual deploy

The workflow supports `workflow_dispatch` — you can trigger a full test + deploy run manually at any time from the GitHub Actions UI without pushing any code:

1. Go to the GitHub repo → **Actions** tab
2. Select the **CI/CD** workflow in the left sidebar
3. Click **Run workflow** → **Run workflow**

This is useful when you've made data-only changes (tag renames, snapshot updates) that don't touch any code file and therefore don't trigger the path filters automatically.

### Snapshot commits and `[skip ci]`

Every admin write (editing a project, uploading media, renaming a tag) automatically commits an updated `admin_snapshot.json` to GitHub with the message `data: update admin snapshot [skip ci]`. The `[skip ci]` flag tells GitHub Actions to skip the workflow entirely for that commit — no tests run, no deploy triggers.

This is intentional. Snapshot commits are data backups, not code changes. They don't need to be tested or deployed independently. When a real code change is pushed next, the deploy step pulls the latest snapshot (including any admin changes made since the last deploy) before uploading to Railway.

To enable Railway deployment from the pipeline, add a `RAILWAY_PORTFOLIO_TOKEN` secret to the GitHub repository (Settings → Secrets and variables → Actions). The token must be a **project-level** token generated from Railway's project settings, not an account API token.

---

## API Reference

Full interactive documentation is available at `/api` on the live site.

### Projects

```bash
# All projects
curl https://xavieroc.dev/api/v1/projects

# Filter by category
curl https://xavieroc.dev/api/v1/projects?category=web
curl https://xavieroc.dev/api/v1/projects?category=data
curl https://xavieroc.dev/api/v1/projects?category=software

# Featured projects only
curl https://xavieroc.dev/api/v1/projects?featured=true

# Filter by tag
curl https://xavieroc.dev/api/v1/projects?tag=machine-learning

# Single project
curl https://xavieroc.dev/api/v1/projects/higher-lower-web-game
```

### Taxonomy

```bash
curl https://xavieroc.dev/api/v1/categories
curl https://xavieroc.dev/api/v1/tags
```

### Response shape

```json
{
  "success": true,
  "data": [
    {
      "title": "Higher Lower Web Game",
      "slug": "higher-lower-web-game",
      "summary": "A browser-based guessing game built with Flask.",
      "category": "web",
      "tags": ["flask", "web-app", "game"],
      "tech_stack": ["Python", "Flask", "Bootstrap"],
      "github_url": "https://github.com/...",
      "live_url": "https://...",
      "featured": true,
      "card_image": "images/projects/...",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "count": 1
}
```

---

## Deployment

The application is deployed on [Railway](https://railway.app).

Railway reads `railway.toml` at the repo root. On every deploy it runs:
```
python -m app.seed_projects && gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

This seeds or updates the database before starting the server.

Required environment variables on Railway: `SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_URL` (provided automatically by Railway's PostgreSQL plugin), and any optional variables for email, analytics, and SEO.

---

## Design Decisions Worth Noting

**Why a REST API on a portfolio?**
Separation of concerns. The Jinja2 templates are one consumer of the project data — not the only possible one. The API makes the data layer explicit and independently accessible. It also powers the live client-side filtering on the projects page.

**Why a custom admin dashboard instead of Flask-Admin or similar?**
Flask-Admin generates a generic CRUD interface. This dashboard is purpose-built for a portfolio — it only exposes what matters (projects, media, tags, messages, backups) in the way that makes sense for this content. It is also a demonstration of building auth-protected admin tooling from scratch.

**Why automated backups before every write?**
The admin is the only interface that modifies production data. A bug in a delete route or an accidental confirmation would be unrecoverable without backups. The backup runs before the write — not after — so a partial failure still leaves a clean snapshot.

**Why is the snapshot sync authoritative?**
On startup in development, the app syncs its local database from `admin_snapshot.json`. The sync is authoritative — projects in the database that are absent from the snapshot are deleted, not preserved. This ensures that deletions made on the live site (which commit an updated snapshot to GitHub) are reflected locally after a `git pull`, without any manual database cleanup.

**Why does the deploy step pull the latest snapshot before uploading?**
The CI/CD workflow is triggered by code changes, not data changes. Between two code pushes, the admin may have committed several snapshot updates (tagged `[skip ci]`). Without a `git pull` in the deploy job, the runner would upload the snapshot as of the triggering commit — potentially missing recent admin edits. The pull step ensures the deploy always includes the most current snapshot, keeping the Railway database in sync with the latest admin state.

**Why is filtering client-side?**
The projects page fetches the full project list once from `/api/v1/projects` on load and caches it in memory. Every subsequent filter or sort is instant — no network round-trip, no page reload. This architecture also demonstrates that the API can serve as the data source for a decoupled front end.

---

## Built As Part Of

This project was built during [100 Days of Code](https://www.100daysofcode.com/) — specifically Days 81–90 (Phase 9). It represents the capstone output of a structured learning curriculum covering Flask, SQLAlchemy, REST API design, admin dashboard development, deployment, and DevOps fundamentals.
