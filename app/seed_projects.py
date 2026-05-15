"""
seed_projects.py

Populate the portfolio database on deploy.

Priority order:
1. app/data/admin_snapshot.json  — written by the admin panel on every change,
   committed to GitHub automatically. When present this is the full source of
   truth for all existing projects (text, tags, media paths, everything).
2. app/data/projects.py          — fallback / source for projects that are not
   yet in the snapshot (e.g. newly added entries).

On every deploy:
- Projects present in the snapshot are restored exactly as they were when the
  admin last saved them (descriptions, tags, media paths, etc.).
- Projects in projects.py that are NOT in the snapshot are inserted fresh
  (new projects added in code that haven't been touched in the admin yet).
- Projects no longer in either source are deleted from the DB.

Run from repo root:
    python -m app.seed_projects
"""

from __future__ import annotations

import json
from pathlib import Path

from app.app import create_app
from app.data.projects import PROJECTS
from app.models.models import Project, db


def _upsert_from_snapshot(existing: Project | None, data: dict) -> Project:
    """Apply fields from a snapshot project dict onto a Project instance.

    For existing projects, admin-managed fields (featured, featured_order,
    card_image, screenshots, videos) are preserved from the DB so that
    admin changes survive deploys. These fields are only set for new projects.
    """
    p = existing or Project()
    p.slug = data["slug"]
    p.title = data["title"]
    p.primary_category = data["primary_category"]
    p.short_description = data["short_description"]
    p.full_description = data["full_description"]
    p.date = data.get("date")
    p.problem = data.get("problem")
    p.solution = data.get("solution")
    p.challenges = data.get("challenges")
    p.results = data.get("results")
    p.tags = data.get("tags", [])
    p.tech_stack = data.get("tech_stack", [])
    p.repo_url = data.get("repo_url")
    p.live_url = data.get("live_url")
    p.demo_url = data.get("demo_url")

    if existing is None:
        # New project — apply all fields from snapshot including admin-managed ones
        p.featured = data.get("featured", False)
        p.featured_order = data.get("featured_order")
        p.card_image = data.get("card_image")
        p.screenshots = data.get("screenshots", [])
        p.videos = data.get("videos", [])

    return p


def seed_projects() -> None:
    app = create_app()

    with app.app_context():
        snapshot_path = Path(app.root_path) / "data" / "admin_snapshot.json"

        # Load snapshot if it exists
        snapshot_projects: list[dict] = []
        if snapshot_path.exists():
            try:
                snapshot_projects = json.loads(snapshot_path.read_text()).get("projects", [])
                print(f"Using admin_snapshot.json ({len(snapshot_projects)} projects).")
            except (json.JSONDecodeError, OSError):
                print("Warning: admin_snapshot.json could not be read — falling back to projects.py.")

        snapshot_slugs = {p["slug"] for p in snapshot_projects}
        seed_slugs = {p["slug"] for p in PROJECTS}

        # Only remove projects that were defined in projects.py but are no longer
        # in the snapshot (i.e. explicitly deleted via admin). Admin-created projects
        # (not in projects.py) are never auto-deleted here — they can only be removed
        # by the admin panel, which deletes them from the DB directly.
        removed_from_seed = seed_slugs - snapshot_slugs
        if removed_from_seed:
            Project.query.filter(Project.slug.in_(removed_from_seed)).delete(
                synchronize_session=False
            )

        # Restore all projects from the snapshot (authoritative for everything)
        for data in snapshot_projects:
            existing = Project.query.filter_by(slug=data["slug"]).first()
            p = _upsert_from_snapshot(existing, data)
            if existing is None:
                db.session.add(p)

        # Insert projects from projects.py that are not yet in the snapshot
        for project_data in PROJECTS:
            if project_data["slug"] in snapshot_slugs:
                continue  # already handled above

            links = project_data.get("links", {})
            media = project_data.get("media", {})
            existing = Project.query.filter_by(slug=project_data["slug"]).first()

            if existing:
                # Update text fields only; preserve admin-managed fields in DB
                existing.title = project_data["title"]
                existing.primary_category = project_data["primary_category"]
                existing.short_description = project_data["short_description"]
                existing.full_description = project_data["full_description"]
                existing.date = project_data.get("date")
                existing.problem = project_data.get("problem")
                existing.solution = project_data.get("solution")
                existing.challenges = project_data.get("challenges")
                existing.results = project_data.get("results")
                existing.repo_url = links.get("repo")
                existing.live_url = links.get("live")
                existing.demo_url = links.get("demo")
                existing.tags = project_data.get("tags", [])
                existing.tech_stack = project_data.get("tech_stack", [])
            else:
                project = Project(
                    slug=project_data["slug"],
                    title=project_data["title"],
                    primary_category=project_data["primary_category"],
                    short_description=project_data["short_description"],
                    full_description=project_data["full_description"],
                    featured=project_data.get("featured", False),
                    date=project_data.get("date"),
                    problem=project_data.get("problem"),
                    solution=project_data.get("solution"),
                    challenges=project_data.get("challenges"),
                    results=project_data.get("results"),
                    repo_url=links.get("repo"),
                    live_url=links.get("live"),
                    demo_url=links.get("demo"),
                    card_image=media.get("card_image"),
                )
                project.tags = project_data.get("tags", [])
                project.tech_stack = project_data.get("tech_stack", [])
                project.screenshots = media.get("screenshots", [])
                project.videos = media.get("videos", [])
                db.session.add(project)

        db.session.commit()

        total = Project.query.count()
        print(f"Database seeded successfully with {total} projects.")


if __name__ == "__main__":
    seed_projects()
