"""
local_seed.py

Syncs your local SQLite database with the latest snapshot from GitHub.

In plain terms:
    When you pull new changes, the projects in your local database don't update
    automatically — the .db file is gitignored and never tracked. This script
    reads admin_snapshot.json (which IS tracked) and rebuilds the local database
    to match it exactly. Run it after every git pull to stay in sync.

Why not just use seed_projects.py?
    seed_projects.py is the deploy-time seeder. It reads DATABASE_URL from your
    .env file and writes to the production PostgreSQL database on Railway.
    This script blanks out DATABASE_URL before anything loads, so it always
    targets the local SQLite file instead.

Run from repo root:
    python -m app.local_seed
"""

import os
import json
from pathlib import Path

# Blank out DATABASE_URL before importing anything from the app.
# config.py calls load_dotenv() at import time, which would otherwise read the
# Railway PostgreSQL URL from .env and point the app at the production database.
# Setting the var here first means load_dotenv() sees it as already set and
# leaves it alone — so the app falls back to the local SQLite file.
os.environ["DATABASE_URL"] = ""

from app.app import create_app
from app.models.models import Project, db
from app.seed_projects import _upsert_from_snapshot


def local_seed() -> None:
    app = create_app()

    with app.app_context():
        snapshot_path = Path(app.root_path) / "data" / "admin_snapshot.json"
        snapshot_projects = json.loads(snapshot_path.read_text()).get("projects", [])
        snapshot_slugs = {p["slug"] for p in snapshot_projects}

        # Remove any projects in the local DB that are no longer in the snapshot
        Project.query.filter(Project.slug.notin_(snapshot_slugs)).delete(
            synchronize_session=False
        )

        # Insert or update every project from the snapshot
        for data in snapshot_projects:
            existing = Project.query.filter_by(slug=data["slug"]).first()
            p = _upsert_from_snapshot(existing, data)
            if existing is None:
                db.session.add(p)

        db.session.commit()
        print(f"Local DB seeded with {Project.query.count()} projects from snapshot.")


if __name__ == "__main__":
    local_seed()
