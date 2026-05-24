"""
app/migrate_to_r2.py

One-time migration script: uploads all project images from
app/static/images/projects/ to Cloudflare R2 and updates the database so
card_image and screenshots store the full R2 public URL instead of a
Flask static-file relative path.

Run once from the repo root after setting R2_* environment variables:

    python -m app.migrate_to_r2

The script is idempotent: values that are already R2 URLs are skipped.
Local files are NOT deleted — remove them manually (or let .gitignore handle
them) once you have confirmed the migration worked.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.app import create_app          # noqa: E402
from app.models.models import Project, db  # noqa: E402
from app import r2                      # noqa: E402


def _migrate_value(value: str, static_dir: Path) -> str | None:
    """
    If *value* is a relative static path that exists on disk, upload it and
    return the R2 URL.  Return None if it is already an R2 URL or the file
    cannot be found.
    """
    if not value or r2.is_r2_url(value):
        return None  # already migrated or empty

    local_path = static_dir / value
    if not local_path.exists():
        print(f"  SKIP (not found): {value}")
        return None

    key = value  # keep same path structure as R2 key
    url = r2.upload_path(local_path, key)
    print(f"  ✓  {value}")
    return url


def _write_snapshot(app) -> None:
    """Overwrite admin_snapshot.json with the current DB state (R2 URLs included)."""
    from app.models.models import ContactMessage
    projects = Project.query.order_by(Project.id.asc()).all()
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    data = {
        "snapshot_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "projects": [
            {
                "id": p.id, "slug": p.slug, "title": p.title,
                "primary_category": p.primary_category,
                "short_description": p.short_description,
                "full_description": p.full_description,
                "featured": p.featured, "featured_order": p.featured_order,
                "date": p.date, "problem": p.problem, "solution": p.solution,
                "challenges": p.challenges, "results": p.results,
                "tags": p.tags, "tech_stack": p.tech_stack,
                "screenshots": p.screenshots, "videos": p.videos,
                "card_image": p.card_image, "repo_url": p.repo_url,
                "live_url": p.live_url, "demo_url": p.demo_url,
            }
            for p in projects
        ],
        "messages": [
            {"id": m.id, "name": m.name, "email": m.email, "message": m.message,
             "created_at": m.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")}
            for m in messages
        ],
    }
    snapshot_path = Path(app.root_path) / "data" / "admin_snapshot.json"
    snapshot_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def run() -> None:
    app = create_app()
    static_dir = Path(app.root_path) / "static"

    with app.app_context():
        projects = Project.query.all()
        updated = 0

        for project in projects:
            changed = False

            # Card image
            if project.card_image:
                new_url = _migrate_value(project.card_image, static_dir)
                if new_url:
                    print(f"[{project.slug}] card_image →")
                    project.card_image = new_url
                    changed = True

            # Screenshots
            new_shots = []
            for shot in project.screenshots:
                new_url = _migrate_value(shot, static_dir)
                if new_url:
                    print(f"[{project.slug}] screenshot →")
                    new_shots.append(new_url)
                else:
                    new_shots.append(shot)  # keep as-is (already R2 or missing)
            if new_shots != project.screenshots:
                project.screenshots = new_shots
                changed = True

            if changed:
                updated += 1

        db.session.commit()
        print(f"\nDone. {updated} project(s) updated in DB.")

        # Also write updated snapshot so local dev (DEBUG sync) and
        # restore-from-snapshot both get R2 URLs.
        _write_snapshot(app)
        print("Snapshot updated with R2 URLs — commit app/data/admin_snapshot.json to git.")


if __name__ == "__main__":
    run()
